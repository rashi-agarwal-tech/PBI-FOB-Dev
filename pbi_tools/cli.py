import typer
from itertools import islice
from pbi_tools.api.auth import get_token, MSAuthToken, get_user_token
from pbi_tools.api.dataset import MSApiDataset
from pbi_tools.api.xmla import PowerBIDaxQuery, PowerBIParameters
from pbi_tools.api.git import MSApiFabric
from pbi_tools.partitions import partition_utils
from pbi_tools.utils.constants import (
    PBI_STATUS_MAP,
    REPORT_DIR,
    PARTITIONS_DIR,
    PBI_META_FILE,
    PBI_AS_ENGINE_ID,
)
from typing import List
from pbi_tools import tmdl
from rich import print
from typing_extensions import Annotated
from rich.console import Console
from rich.table import Table, box
from rich.text import Text
import json
import networkx as nx
from collections import defaultdict
from pbi_tools.dax.query import get_event_query

app = typer.Typer()
console = Console()


def chunks(data, size=10000):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def non_zero_variables() -> list[str]:
    return [m for m, v in tmdl.get_variable_values("NumberOfRows").items() if v != "0"]


@app.command()
def check_num_rows_vars_zero() -> str:
    non_zero = non_zero_variables()
    if non_zero:
        print(
            f"Warning: Non-zero NumberOfRows variable detected in the following models: {non_zero}."
        )
    else:
        print("Success: All NumberOfRows set to zero.")


def check_tables_partitioned() -> dict | None:
    models = tmdl.get_models()
    result = defaultdict(list)
    for m, tables in models.items():
        for t, details in tables.items():
            if (
                details["partitioned"] is False
                and details["multi_partition_expected"] is True
            ):
                result[m].append(t)
    return result


@app.command()
def check_partitions() -> str:
    result = check_tables_partitioned()
    if result:
        print(f"Warning: The following tables have missing partitions: {dict(result)}.")
    else:
        print("Success: All tables partitioned.")


@app.command()
def swap_partitions(original: bool = True):
    tmdl.set_variable("NumberOfRows", "1000" if original else "0")
    tmdl.set_variable(
        "Datasource_Server", '"drmartensdev.west-europe.azure.snowflakecomputing.com"'
    )
    for workspace in PARTITIONS_DIR.iterdir():
        for partition_dir in workspace.iterdir():
            for table_dir in partition_dir.iterdir():
                tmdl_file = (
                    REPORT_DIR
                    / workspace.name
                    / f"{partition_dir.name}.SemanticModel"
                    / "definition"
                    / "tables"
                    / f"{table_dir.name}.tmdl"
                )
                line_no, tmdl_str, partitions_str = tmdl.remove_partitions(tmdl_file)
                # This is a crude approximation as by default PBI will add a unique 36 character hash to the name of the partition
                default_partition = (
                    True
                    if len(tmdl.get_first_partition_name(partitions_str)) > 38
                    else False
                )
                if not default_partition:
                    (table_dir / "partitions.tmdl").write_text(partitions_str)
                partition_file = (
                    (table_dir / "original.tmdl")
                    if original
                    else (table_dir / "partitions.tmdl")
                )
                partitions_str = partition_file.read_text()
                tmdl_final_text = tmdl.add_partitions(tmdl_str, partitions_str, line_no)
                tmdl_file.write_text(tmdl_final_text)
    print(
        "Multi partitions removed, ready for editing"
        if original
        else "Multi partitions restored for publishing"
    )


@app.command()
def partitions():
    print(tmdl.get_multi_partitions())
    print(tmdl.get_expected_partitions())


@app.command()
def print_models(write: bool = False):
    print(tmdl.get_models(write))


@app.command()
def save_meta_pbi_tools():
    PBI_META_FILE.write_text(json.dumps(tmdl.get_models()))


@app.command()
def save_model_metadata_db():
    import pbi_tools.utils.sn_connector as sn
    from snowflake.connector.pandas_tools import write_pandas
    import pandas as pd

    models = tmdl.get_models()
    models_flat = [
        (k, t, c) for k, v in models.items() for t, p in v.items() for c in p["columns"]
    ]
    sn_con = sn.get_snowflake_connection()
    models_df = pd.DataFrame(
        models_flat, columns=["DATASET_NAME", "TABLE_NAME", "FIELD_NAME"]
    )
    print(models_df.shape)
    print(models_df.head())
    write_pandas(sn_con, models_df, "POWERBI_FIELDS")
    sn_con.close()
    print(models_flat)


@app.command()
def order_tables():
    for f in REPORT_DIR.glob("**/model.tmdl"):
        lines = f.read_text().split("\n")
        for i, line in enumerate(lines):
            if line.startswith("annotation PBI_QueryOrder ="):
                tables = eval(line[28:])
                tables.sort()
                lines[i] = f"annotation PBI_QueryOrder = {tables}".replace("'", '"')
        f.write_text("\n".join(lines))


@app.command()
def print_params():
    print(tmdl.get_model_parameters())


@app.command()
def get_relation_between(model, table_a, table_b, graph: bool = False):
    G = tmdl.create_relationship_graph(model)
    nodes = nx.shortest_path(G, table_a, table_b, 5)
    if graph:
        tmdl.plot_relationships(G.subgraph(nodes), f"{model}: {table_a} to {table_b}")
    else:
        tmdl.print_relationship_between(G, nodes)


@app.command()
def plot_table_relationships(model, table: str = None):
    G = tmdl.create_relationship_graph(model)
    if table:
        tmdl.plot_relationships(tmdl.get_neighbors_graph(G, table), f"{model}: {table}")
    else:
        tmdl.plot_relationships(G, f"{model}")


@app.command()
def refresh_d2c(env: str = "dev"):
    refresh_d2c_availability_partition(env)
    refresh_d2c_orders_partition(env)
    refresh_d2c_tables(env)


@app.command()
def get_params(env: str = "dev"):
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset="DMA D2C",
    )
    print(refresh_api.get_parameters())


@app.command()
def update_params(dataset: str, env: str = "dev"):
    from pbi_tools.api.xmla import PowerBIParameters

    refresh_api = MSApiDataset(token=get_token(), dataset=dataset, workspace_env=env)
    print(refresh_api.update_parameters(PowerBIParameters([("NumberOfRows", "0")])))


@app.command()
def refresh_d2c_tables(env: str = "dev", dataset: str = "DMA D2C"):
    tables = chunks(
        data=partition_utils.get_tables(dataset, partitioned=False), size=20
    )
    for t in tables:
        refresh_api = MSApiDataset(
            token=get_token(),
            dataset=dataset,
            table_partition=t,
            workspace_env=env,
            poll_time=60,
            commit_mode="partialBatch",
            max_parallelism=30,
        )
        refresh_api.refresh_dataset()
        refresh_api.poll_status()


@app.command()
def cancel_refresh(dataset: str, env: str = "dev"):
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset=dataset,
        workspace_env=env,
        poll_time=60,
    )
    refresh_api.cancel_refresh()
    refresh_api.poll_status()


@app.command()
def refresh_d2c_orders_partition(
    env: str = "dev",
    current: bool = True,
    dataset: str = "DMA D2C",
    partition: str = "",
):
    if partition != "":
        parts = [partition]
    elif current is True:
        parts = [partition_utils.get_latest_fy_partition()]
    else:
        # Need a function to get all partitions for a table and dataset.
        # Below does not currently work!
        parts = partition_utils.get_tables()

    for p in parts:
        refresh_api = MSApiDataset(
            token=get_token(),
            dataset=dataset,
            table_partition={"Orders": [p]},
            workspace_env=env,
            poll_time=120,
            commit_mode="partialBatch",
            max_parallelism=20,
        )
        refresh_api.refresh_dataset()
        refresh_api.poll_status()


@app.command()
def refresh_dataset(dataset: str, env: str = "dev", poll: bool = True):
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset=dataset,
        workspace_env=env,
        poll_time=120,
        commit_mode="partialBatch",
        max_parallelism=20,
    )
    refresh_api.refresh_dataset()
    if poll:
        refresh_api.poll_status()


@app.command()
def refresh_d2c_partitions(env: str = "dev"):
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset="DMA D2C",
        table_partition={
            "Availability": [partition_utils.get_latest_cy_mm_partition()],
            "Orders": [partition_utils.get_latest_fy_partition()],
        },
        workspace_env=env,
        commit_mode="partialBatch",
        max_parallelism=20,
        poll_time=120,
    )
    refresh_api.refresh_dataset()
    refresh_api.poll_status()


@app.command()
def refresh_d2c_availability_partition(env: str = "dev", current: bool = True):
    if current is True:
        parts = [partition_utils.get_latest_cy_mm_partition()]
    else:
        # Need a function to get all partition of a table for a dataset.
        parts = partition_utils.get_latest_cy_mm_partition()
    for p in parts:
        refresh_api = MSApiDataset(
            token=get_token(),
            dataset="DMA D2C",
            table_partition={
                "Availability": [p],
            },
            workspace_env=env,
            commit_mode="partialBatch",
            max_parallelism=20,
            poll_time=120,
        )
        refresh_api.refresh_dataset()
        refresh_api.poll_status()


@app.command()
def refresh_partition(
    dataset: str,
    table: str,
    partition: str = None,
    env: str = "dev",
):
    if partition is None:
        partition = [partition_utils.get_latest_cy_mm_partition()]
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset=dataset,
        table_partition={
            table: [partition],
        },
        workspace_env=env,
        commit_mode="partialBatch",
        max_parallelism=20,
        poll_time=120,
    )
    refresh_api.refresh_dataset()
    refresh_api.poll_status()


@app.command()
def xmla_body(env: str = "dev"):
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset="DMA D2C",
        table_partition={"Orders": []},
        workspace_env=env,
        poll_time=10,
    )
    print(refresh_api.get_xmla_body())


@app.command()
def list_tables(dataset: str, env: str = "dev"):
    refresh_api = MSApiDataset(
        token=get_token(),
        dataset=dataset,
        workspace_env=env,
    )
    print(
        refresh_api.execute_query(
            PowerBIDaxQuery(
                """select * from $system.DBSCHEMA_TABLES
                    where table_type = 'TABLE'"""
            )
        )
    )


@app.command()
def get_queries():
    from pbi_tools.api.auth import get_user_token
    from pbi_tools.api.dax_query import MSApiQuery

    MSApiQuery(token=get_user_token()).execute_query(
        PBI_AS_ENGINE_ID, get_event_query(10, 12, 2024, 12, 8)
    )


def get_rowcount_dax(
    table: str,
    filter_column: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    return f"""  DEFINE
                VAR _rows = COUNTROWS ( FILTER({table}, {table}[{filter_column}] > 10) )
                EVALUATE
                SELECTCOLUMNS ( { 1 }, "Rows", _rows )"""


@app.command()
def status(
    dataset: Annotated[str, typer.Option(prompt=True)],
    env: str = "dev",
    poll: bool = False,
    num_results: int = 5,
    print_as_table: bool = True,
    token: str = None,
):
    status, refresh_api = get_status(dataset, env, num_results, token)
    if print_as_table:
        print_table(status)
    else:
        print(status)
    if poll is True:
        print("Polling for status")
        refresh_api.poll_status()


def get_status(
    dataset: str,
    env: str = "dev",
    num_results: int = 1,
    token: MSAuthToken | None = None,
):
    if token is None:
        token = get_token()
    refresh_api = MSApiDataset(token=token, dataset=dataset, workspace_env=env)
    statuses = [
        {"name": dataset} | s
        for s in refresh_api.get_top_n_refresh(n=num_results, get_details=True)
    ]
    return statuses, refresh_api


@app.command()
def status_all(env: str = "dev", table=True):
    pass


def get_status_all(
    env: str = "dev", models: List[str] | None = None, num_results: int = 1
):
    models = [m["name"] for m in tmdl.get_models(env=env)] if models is None else models
    statuses = [get_status(m, env, num_results=num_results)[0] for m in models]
    return [i for s in statuses for i in s]


def print_table(status: list[dict], collapse_batches: bool = True) -> None:
    status = flatten_status(status)
    status_colour = {
        "Completed": "green",
        "Running": "yellow",
        "Failed": "red",
        "In Progress": "blue",
    }
    tbl = Table(
        "Name",
        "Table",
        "Partition",
        "Start",
        "End",
        "Status",
        box=box.MINIMAL_DOUBLE_HEAD,
        row_styles=["dim", ""],
    )
    for r in status:
        tbl.add_row(
            r.get("name", "Not Found"),
            r.get("table", "Not Found"),
            r.get("partition", "Not Found"),
            r.get("startTime", "Not Found"),
            r.get("endTime", "Not Found"),
            Text(
                status := PBI_STATUS_MAP[r.get("status")],
                style=status_colour.get(status, ""),
            ),
        )
    console.print(tbl)


def print_as_table(status: list[dict]) -> None:
    pass


def flatten_status(status: list[dict]) -> list[dict] | None:
    results = []
    if status is None:
        return None
    for r in status:
        if r.get("extendedDetails"):
            for o in r["extendedDetails"]["objects"]:
                results.append(
                    {
                        "name": r["name"],
                        "table": o["table"],
                        "partition": (
                            o["partition"] if len(o["partition"]) < 37 else "Full"
                        ),
                        "startTime": r["startTime"],
                        "endTime": r.get("endTime"),
                        "status": o["status"],
                    }
                )
        else:
            results.append(
                {
                    "name": r["name"],
                    "table": "*",
                    "partition": "Full",
                    "startTime": r["startTime"],
                    "endTime": r.get("endTime"),
                    "status": r["status"],
                }
            )
    return results


@app.command()
def d2c_status(env: str = "dev", num_results: int = 10, collapse_batches: bool = True):
    refresh_api = MSApiDataset(token=get_token(), dataset="DMA D2C", workspace_env=env)
    refreshes = refresh_api.get_top_n_refresh(n=num_results, get_details=True)
    print_table(refreshes, collapse_batches)


@app.command()
def get_parameters(dataset: str, env: str = "dev"):
    refresh_api = MSApiDataset(token=get_token(), dataset=dataset, workspace_env=env)
    print(refresh_api.get_parameters())


@app.command()
def set_parameter(dataset: str, param: str, value: str, env: str = "dev"):
    refresh_api = MSApiDataset(token=get_token(), dataset=dataset, workspace_env=env)
    refresh_api.update_parameters(PowerBIParameters([(param, value)]))


@app.command()
def sync_workspace_git(env: str = "dev"):
    git = MSApiFabric(token=get_user_token(), workspace_env=env)
    print(git.sync_workspace_git())


if __name__ == "__main__":
    app()
    # refresh_d2c_availability_partition("dev", current=False)
    # swap_partitions(original=False)
    # partitions()
    # status_all()
    # TODO Parameters, set number of row if exists to some number!
    # TODO Can we ensure that "Large semantic model storage format" is on...
    # TODO Can we get a list of tables / objects in a dataset? Only via dax, permissions.
    # TODO Add logic to look for advanced refresh and return detailed refresh as well.
    # TODO View and set Parameters. Permissions issue?
    # TODO Set / ensure {
    #   "targetStorageMode": "PremiumFiles"
    # }  PATCH https://api.powerbi.com/v1.0/myorg/groups/{groupId}/datasets/{datasetId}
    # TODO Can we create a partition, test with datasets url and body...
    # TODO if we can do above, how to automate creation of these partitions
    # TODO Can we view partitions?
    # TODO Add logging.....


# Get Partitions, execute DAX
#     select * from $system.TMSCHEMA_PARTITIONS
# where mode = 2;
# get tables via dax
#     select * from $system.DBSCHEMA_TABLES
# where table_type = 'TABLE';

# Can you create a partition with dax? Does not look like it....


# Parameters that need to be set dynamically.
# env = "prod"

# NumberOfRows = 0
# Datasource_Server = f"drmartens{env}.west-europe.azure.snowflakecomputing.com"
# Datasource_Warehouse = "REPORTER"
# COUNTROWS('Orders')
