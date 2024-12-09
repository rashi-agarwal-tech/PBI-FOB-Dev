from airflow.models.baseoperator import BaseOperator
from pbi_tools.api.dataset import MSApiDataset
from pbi_tools.utils.constants import ENV
from typing import Literal
from airflow.providers.common.sql.hooks.sql import DbApiHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from pbi_tools.utils import load_pbi_fields
from pbi_tools.api.auth import get_token
from datetime import datetime
from pbi_tools.sql.powerbi_field_usage import (
    get_merge_sql,
    get_create_temp_tbl_sql,
    get_unique_str,
)
import logging
from pathlib import Path
import os


TEMP_VOLUME = (
    Path(os.getenv("AIRFLOW_HOME"), "/opt/airflow") / "data" / "pbi_metadata" / "temp"
)
TEMP_VOLUME.mkdir(exist_ok=True, parents=True)


class PowerBIRefreshOperator(BaseOperator):
    def __init__(
        self,
        dataset: str,
        table_partition: dict[list] | None = None,
        commit_mode: Literal["transactional", "partialBatch"] = "transactional",
        max_parallelism: str = "10",
        poll_time: int = 10,
        env: ENV | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.dataset = dataset
        self.table_partition = table_partition
        self.commit_mode = commit_mode
        self.max_parallelism = max_parallelism
        self.poll_time = poll_time
        self.env = env

    def execute(self, context):
        refresh_api = MSApiDataset(
            token=get_token(),
            dataset=self.dataset,
            table_partition=self.table_partition,
            workspace_env=self.env,
            poll_time=self.poll_time,
            max_parallelism=self.max_parallelism,
        )

        refresh_api.refresh_dataset()
        status = refresh_api.poll_status()
        if status != "Completed":
            raise ValueError(
                f"Refresh of {self.dataset} failed: {refresh_api.get_latest_refresh()}"
            )
        return


class PowerBIFieldUsageOperator(BaseOperator):
    template_fields = ("date",)

    def __init__(
        self,
        delta_days: int = 0,
        db_api_hook: DbApiHook = SnowflakeHook(
            snowflake_conn_id="snowflake",
            session_parameters={"CLIENT_SESSION_KEEP_ALIVE": True},
        ),
        date: datetime = datetime.now(),
        fq_table_name: str = "MONITORING.LOGS.POWERBI_FIELD_USAGE",
        temp_file_path: Path = TEMP_VOLUME,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.day_delta = delta_days
        self.db_api_hook = db_api_hook
        self.date = date
        self.tmp_tbl = f"{fq_table_name}_{get_unique_str()}"
        self.temp_file_name = f"{self.tmp_tbl}.csv"
        self.fq_temp_file = temp_file_path / self.temp_file_name
        self.fq_table_name = fq_table_name

    def execute(self, context):
        import csv

        logging.info("Fetching data from Power BI Metadata Model")
        data = load_pbi_fields.extract_fields(date=self.date, delta_days=self.day_delta)
        num_records = len(data)
        logging.info(
            f"Data retrieved: {num_records}\nCreating temp table: {self.tmp_tbl}"
        )

        if num_records == 0:
            return {"message": "No records retrieved"}
        try:
            self.db_api_hook.run(
                get_create_temp_tbl_sql(self.fq_table_name, self.tmp_tbl),
                autocommit=True,
            )
            logging.info(f"Inserting records into {self.tmp_tbl}")
            with self.fq_temp_file.open(mode="w", newline="") as f_in:
                writer = csv.writer(f_in, delimiter=",", quoting=csv.QUOTE_MINIMAL)
                writer.writerows(data)

            self.db_api_hook.run(f"PUT file://{self.fq_temp_file.as_posix()} @~")
            self.db_api_hook.run(
                f"COPY INTO {self.tmp_tbl} FROM @~/{self.temp_file_name} FILE_FORMAT = (type = 'CSV')"
            )
            logging.info(f"Merging records into {self.fq_table_name}")
            self.db_api_hook.run(
                get_merge_sql(
                    source_tbl_name=self.tmp_tbl, target_tbl_name=self.fq_table_name
                ),
                autocommit=True,
            )
        finally:
            logging.info(f"Removing Stage: {self.temp_file_name}")
            self.db_api_hook.run(f"REMOVE @~/{self.temp_file_name}")
            logging.info(f"Removing Local File: {self.fq_temp_file}")
            if self.fq_temp_file.exists():
                self.fq_temp_file.unlink()
            logging.info(f"Dropping table: {self.tmp_tbl}")
            self.db_api_hook.run(f"DROP TABLE {self.tmp_tbl}", autocommit=True)
        return {
            "table_name": self.fq_table_name,
            "records_inserted": num_records,
            "temp_table": self.tmp_tbl,
            "temp_stage_file": self.temp_file_name,
        }
