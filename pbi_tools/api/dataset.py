import time
from typing import Literal, List
from dataclasses import dataclass
from pprint import pp
from pbi_tools.api import xmla
from pbi_tools.api.workspace import MSApiWorkspace


@dataclass(kw_only=True)
class MSApiDataset(MSApiWorkspace):
    dataset: str
    table_partition: dict[List] | None = None
    dataset_id: str | None = None
    max_parallelism: int = 10
    commit_mode: Literal["transactional", "partialBatch"] = "transactional"

    status_list = ["Unknown", "Disabled", "Failed", "Completed"]

    def __post_init__(self):
        super().__post_init__()
        self.datasets_url = self.get_datasets_url()
        self.dataset_id = (
            self.get_dataset_id() if self.dataset_id is None else self.dataset_id
        )
        self.refresh_url = self.get_refresh_url()
        self.body_xmla = self.get_xmla_body()

    def get_dataset_id(self, datasets: list[dict] | None = None) -> str:
        if datasets is None:
            datasets = self.get_datasets()
        id = [ds["id"] for ds in datasets if ds["name"] == self.dataset]
        if len(id) == 1:
            return id[0]
        else:
            raise LookupError("Dataset name not found in workgroup")

    def get_datasets_url(
        self,
        workspace_id: str | None = None,
        dataset_id: str | None = None,
        operation: str | None = None,
    ):
        workspace_id = workspace_id if workspace_id else self.workspace_id
        dataset_id = f"/{dataset_id}" if dataset_id else ""
        if operation:
            dataset_id = f"/{self.dataset_id}" if dataset_id == "" else dataset_id
            operation = f"/{operation}"
        else:
            operation = ""
        return f"{self.url}/groups/{workspace_id}/datasets{dataset_id}{operation}"

    def get_refresh_url(
        self, dataset_id: str | None = None, workspace_id: str | None = None
    ):
        return self.get_datasets_url(workspace_id, dataset_id, "refreshes")

    def get_tables_url(
        self, dataset_id: str | None = None, workspace_id: str | None = None
    ):
        """Will only work for "push datasets" """
        return self.get_datasets_url(workspace_id, dataset_id, "tables")

    def get_exec_query_url(
        self, dataset_id: str | None = None, workspace_id: str | None = None
    ):
        return self.get_datasets_url(workspace_id, dataset_id, "executeQueries")

    def get_parameters_url(
        self, dataset_id: str | None = None, workspace_id: str | None = None
    ):
        return self.get_datasets_url(workspace_id, dataset_id, "parameters")

    def update_parameters_url(
        self, dataset_id: str | None = None, workspace_id: str | None = None
    ):
        return self.get_datasets_url(
            workspace_id, dataset_id, "Default.UpdateParameters"
        )

    def execute_query(self, query: xmla.PowerBIDaxQuery | dict):
        body = query if isinstance(query, dict) else query.to_dict()
        return self.post_request(url=self.get_exec_query_url(), body=body)

    def update_parameters(self, param_value: xmla.PowerBIParameters | dict):
        body = param_value if isinstance(param_value, dict) else param_value.to_dict()
        return self.post_request(url=self.update_parameters_url(), body=body)

    def get_tables(self):
        return self.get_request(self.get_tables_url())

    def get_parameters(self):
        return self.get_request(self.get_parameters_url())

    def get_refresh_status(self):
        return self.get_request(self.refresh_url)

    def get_datasets(self):
        return self.get_request(self.datasets_url)

    def get_refresh_details(self, refresh_id: str | None = None):
        if refresh_id is None and self.refresh_id is not None:
            refresh_id = self.refresh_id
        elif refresh_id is None and self.refresh_id is None:
            refresh_id = self.get_latest_refresh_id()
        return self.get_request(self.get_refresh_details_url(refresh_id))

    def get_top_n_refresh(self, n=1, get_details: bool = True) -> list | None:
        status = self.get_refresh_status()
        if isinstance(status, dict):
            return []
        if not isinstance(status, list):
            return None
        statuses = status[:n] if len(status) > n else status
        for s in statuses:
            if get_details is True and s.get("extendedStatus"):
                s["extendedDetails"] = self.get_refresh_details(
                    refresh_id=s["requestId"]
                )
        return statuses

    def get_latest_refresh(self, get_details: bool = False):
        return self.get_top_n_refresh(n=1, get_details=get_details)[0]

    def get_latest_refresh_id(self):
        latest_status = self.get_latest_refresh()
        if latest_status.get("requestId"):
            return latest_status["requestId"]

    def get_refresh_details_url(self, refresh_id):
        if refresh_id is None:
            refresh_id = self.refresh_id
        return f"{self.get_refresh_url()}/{refresh_id}"

    def cancel_refresh(self, refresh_id=None):
        if refresh_id is None:
            refresh_id = self.refresh_id
        if refresh_id is None:
            refresh_id = self.get_latest_refresh_id()
        return self.delete_request(self.get_refresh_details_url(refresh_id))

    def refresh_dataset(self):
        return self.post_request(url=self.refresh_url, body=self.body_xmla)

    def poll_status(self):
        status = "Unknown"
        if self.refresh_id is None:
            self.refresh_id = self.get_latest_refresh_id()
        while status == "Unknown":
            time.sleep(self.poll_time)
            refresh_details = [
                s
                for s in self.get_refresh_status()
                if s["requestId"] == self.refresh_id
            ]
            if len(refresh_details) == 1:
                refresh_details = refresh_details[0]
                pp(refresh_details)
            else:
                pp("Could not get status!")
            if refresh_details.get("extendedStatus"):
                pp(self.get_refresh_details())
            status = refresh_details["status"]

        return status

    def get_xmla_body(self):
        if self.table_partition is None:
            return {}
        tbls_parts = {
            t: [None] if not p else p for t, p in self.table_partition.items()
        }
        xmla_partition = xmla.PowerBIRefreshPartition(
            datasets=[
                xmla.PowerBIDataset(database=self.dataset, table=t, partition=p)
                for t, partitions in tbls_parts.items()
                for p in partitions
            ],
            commit_mode=self.commit_mode,
            max_parallelism=self.max_parallelism,
        ).to_dict()
        return xmla_partition
