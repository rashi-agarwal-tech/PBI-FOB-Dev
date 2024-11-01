import typer
from itertools import islice
from pbi_tools.mspbi_api import (
    PowerBiAPIDataset,
    PowerBiAPIWorkspace,
    PowerBIToken,
)
from pbi_tools.mspbi_xmla import PowerBIDaxQuery, PowerBIParameters
from pprint import pp
from pbi_tools.partitions import d2c_tables
from pbi_tools.constants import PBI_STATUS_MAP
from tabulate import tabulate
from typing import List

app = typer.Typer()


def chunks(data, size=10000):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def get_token() -> PowerBIToken:
    from pbi_tools import load_envs

    return PowerBIToken(
        client_id=load_envs.get_client_id(),
        client_secret=load_envs.get_client_secret(),
        get_token_method="msal",
    )


@app.command()
def refresh_d2c(env: str = "dev"):
    refresh_d2c_availability_partition(env)
    refresh_d2c_orders_partition(env)
    refresh_d2c_tables(env)


@app.command()
def get_params(env: str = "dev"):
    refresh_api = PowerBiAPIDataset(
        token=get_token(),
        dataset="DMA D2C",
    )
    pp(refresh_api.get_parameters())


@app.command()
def update_params(dataset: str, env: str = "dev"):
    from pbi_tools.mspbi_xmla import PowerBIParameters

    refresh_api = PowerBiAPIDataset(
        token=get_token(), dataset=dataset, workspace_env=env
    )
    pp(refresh_api.update_parameters(PowerBIParameters([("NumberOfRows", "0")])))


@app.command()
def refresh_d2c_tables(env: str = "dev", dataset: str = "DMA D2C"):
    tables = chunks(data=d2c_tables.non_partition_tables_dict, size=20)
    for t in tables:
        refresh_api = PowerBiAPIDataset(
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
    refresh_api = PowerBiAPIDataset(
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
        parts = [d2c_tables.get_current_fy_partition()]
    else:
        parts = d2c_tables.partition_tables["Orders"]

    for p in parts:
        refresh_api = PowerBiAPIDataset(
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
    refresh_api = PowerBiAPIDataset(
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
    refresh_api = PowerBiAPIDataset(
        token=get_token(),
        dataset="DMA D2C",
        table_partition={
            "Availability": [d2c_tables.get_current_cy_mm_partition()],
            "Orders": [d2c_tables.get_current_fy_partition()],
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
        parts = [d2c_tables.get_current_cy_mm_partition()]
    else:
        parts = d2c_tables.partition_tables["Availability"]
    for p in parts:
        refresh_api = PowerBiAPIDataset(
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
        partition = [d2c_tables.get_current_cy_mm_partition()]
    refresh_api = PowerBiAPIDataset(
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
def test(
    dataset: str,
    table: str,
    partition: List[str],
    env: str = "dev",
):
    print(partition)


@app.command()
def xmla_body(env: str = "dev"):
    refresh_api = PowerBiAPIDataset(
        token=get_token(),
        dataset="DMA D2C",
        table_partition={"Orders": []},
        workspace_env=env,
        poll_time=10,
    )
    pp(refresh_api.get_xmla_body())


@app.command()
def list_tables(dataset: str, env: str = "dev"):
    refresh_api = PowerBiAPIDataset(
        token=get_token(),
        dataset=dataset,
        workspace_env=env,
    )
    pp(
        refresh_api.execute_query(
            PowerBIDaxQuery(
                """select * from $system.DBSCHEMA_TABLES
                    where table_type = 'TABLE'"""
            )
        )
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
    dataset: str,
    env: str = "dev",
    poll: bool = False,
    num_results: int = 1,
    print_as_table: bool = True,
    token: str = None,
):
    status, refresh_api = get_status(dataset, env, num_results, token)
    if print_as_table:
        print_table(status)
    else:
        pp(status)
    if poll is True:
        print("Polling for status")
        refresh_api.poll_status()


def get_status(
    dataset: str,
    env: str = "dev",
    num_results: int = 1,
    token: PowerBIToken | None = None,
):
    if token is None:
        token = get_token()
    refresh_api = PowerBiAPIDataset(token=token, dataset=dataset, workspace_env=env)
    statuses = [
        {"name": dataset} | s
        for s in refresh_api.get_top_n_refresh(n=num_results, get_details=True)
    ]
    return statuses, refresh_api


@app.command()
def status_all(env: str = "dev", table=True):
    status = get_status_all(env=env)
    print_as_table(status) if table else pp(status)


def get_status_all(
    env: str = "dev", models: List[str] | None = None, num_results: int = 1
):
    models = [m["name"] for m in get_models(env=env)] if models is None else models
    statuses = [get_status(m, env, num_results=num_results)[0] for m in models]
    return [i for s in statuses for i in s]


def get_models(env: str = "dev", token: PowerBIToken | None = None) -> dict:
    if token is None:
        token = get_token()
    return PowerBiAPIWorkspace(token=token, workspace_env=env).get_models()


def print_table(status: list[dict], collapse_batches: bool = True) -> None:
    data = [("Table", "Partition", "Start", "End", "Status")] + [
        (
            r["table"],
            r["partition"],
            r["startTime"],
            r["endTime"],
            PBI_STATUS_MAP[r["status"]],
        )
        for r in status
    ]
    if collapse_batches:
        results = [r for i, r in enumerate(data) if data[i][3] != data[i - 1][3]]
    print(tabulate(results, headers="firstrow", tablefmt="fancy_grid"))


def print_as_table(status: list[dict]) -> None:
    data = [("Model", "Start", "End", "Status")] + [
        (r["name"], r["startTime"], r.get("endTime"), PBI_STATUS_MAP[r["status"]])
        for r in status
    ]
    print(tabulate(data, headers="firstrow", tablefmt="fancy_grid"))


def flatten_status(
    status: list[dict], collapse_batches: bool = True
) -> list[dict] | None:
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
                        "partition": o["partition"]
                        if len(o["partition"]) < 37
                        else "Full",
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
    refresh_api = PowerBiAPIDataset(
        token=get_token(), dataset="DMA D2C", workspace_env=env
    )
    refreshes = refresh_api.get_top_n_refresh(n=num_results, get_details=True)
    print_table(refreshes, collapse_batches)


@app.command()
def get_parameters(dataset: str, env: str = "dev"):
    refresh_api = PowerBiAPIDataset(
        token=get_token(), dataset=dataset, workspace_env=env
    )
    pp(refresh_api.get_parameters())


@app.command()
def set_parameter(dataset: str, param: str, value: str, env: str = "dev"):
    refresh_api = PowerBiAPIDataset(
        token=get_token(), dataset=dataset, workspace_env=env
    )
    refresh_api.update_parameters(PowerBIParameters([(param, value)]))


if __name__ == "__main__":
    # refresh_d2c_availability_partition("dev", current=False)
    app()
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
