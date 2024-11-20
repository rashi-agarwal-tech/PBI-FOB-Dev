from airflow.models.baseoperator import BaseOperator
from pbi_tools.mspbi_api import (
    MSAuthToken,
    MSApiDataset,
    Environment,
)
from typing import Literal
import os


class PowerBIRefreshOperator(BaseOperator):
    def __init__(
        self,
        dataset: str,
        table_partition: dict[list] | None = None,
        commit_mode: Literal["transactional", "partialBatch"] = "transactional",
        max_parallelism: str = "10",
        poll_time: int = 10,
        env: Environment | None = None,
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
        pbi_token = MSAuthToken(
            client_id=os.getenv("client_id"),
            client_secret=os.getenv("client_secret"),
            get_token_method="msal",
        )

        refresh_api = MSApiDataset(
            token=pbi_token,
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
