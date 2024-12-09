import string
import random

table_name = "MONITORING.LOGS.POWERBI_FIELD_USAGE"


def get_merge_sql(source_tbl_name: str, target_tbl_name: str) -> str:
    return f"""MERGE INTO {target_tbl_name} AS TARGET
USING {source_tbl_name} AS SOURCE
ON TARGET.WORKSPACE_NAME = SOURCE.WORKSPACE_NAME
   AND TARGET.DATASET_NAME = SOURCE.DATASET_NAME
   AND TARGET.TABLE_NAME = SOURCE.TABLE_NAME
   AND TARGET.FIELD_NAME = SOURCE.FIELD_NAME
   AND TARGET.QUERY_DATE_HOUR = SOURCE.QUERY_DATE_HOUR
WHEN MATCHED THEN
    UPDATE SET 
        TARGET.USAGE_COUNT = SOURCE.USAGE_COUNT,
        TARGET.UPDATE_DT = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (
        WORKSPACE_NAME, DATASET_NAME, TABLE_NAME, FIELD_NAME, QUERY_DATE_HOUR, USAGE_COUNT, INSERT_DT, UPDATE_DT
    )
    VALUES (
        SOURCE.WORKSPACE_NAME, SOURCE.DATASET_NAME, SOURCE.TABLE_NAME, SOURCE.FIELD_NAME, 
        SOURCE.QUERY_DATE_HOUR, SOURCE.USAGE_COUNT, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
    );"""


def get_create_temp_tbl_sql(table_name: str, temp_table_name: str) -> str:
    return f"""CREATE TABLE {temp_table_name}  AS
    SELECT * EXCLUDE(INSERT_DT, UPDATE_DT) FROM {table_name} LIMIT 0
"""


def get_unique_str(unique_id: str | None = None, length: int = 4):
    return "".join(random.choices(string.ascii_uppercase, k=length))


# Below is created in terraform in windermere repo.
def get_create_tbl_sql(table_name) -> str:
    return f"""CREATE TABLE {table_name} (
    WORKSPACE_NAME STRING NOT NULL,
    DATASET_NAME STRING NOT NULL,
    TABLE_NAME STRING NOT NULL,
    FIELD_NAME STRING NOT NULL,
    QUERY_DATE_HOUR TIMESTAMP NOT NULL,
    USAGE_COUNT INTEGER NOT NULL,
    INSERT_DT TIMESTAMP NOT NULL,
    UPDATE_DT TIMESTAMP NOT NULL
);"""


def get_insert_sql(table_name: str, num_rows: int, num_columns: int):
    columns = "(" + ", ".join(["%s"] * num_columns) + ")"
    values_placeholder = ", ".join([columns] * num_rows)
    return f"INSERT INTO {table_name} VALUES {values_placeholder})"


if __name__ == "__main__":
    print(get_insert_sql("table-name", 3, 5))
