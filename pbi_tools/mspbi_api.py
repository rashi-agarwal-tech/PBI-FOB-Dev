import json
import time
from typing import Literal, List
from dataclasses import dataclass
import requests
from requests import Response
from pprint import pp
from pbi_tools.constants import (
    WORKSPACE_IDS,
    Environment,
    REFRESH_TYPE,
)
from pbi_tools import mspbi_xmla
import logging
from time import sleep
import functools

ATTEMPTS = 5
BACKOFF_FACTOR = 5
# testing some more............................


def backoff_delay(backoff_factor, attempts):
    return [backoff_factor * (2 ** (a)) for a in range(attempts)]


def request_retry(func):
    @functools.wraps(func)
    def wrapper_request(*args, **kwargs):
        for i, wait in enumerate(backoff_delay(BACKOFF_FACTOR, ATTEMPTS)):
            try:
                value = func(*args, **kwargs)
            except Exception as e:
                if i == ATTEMPTS - 1:
                    raise
                logging.warning(f"Error requesting PBI {e}, up for retry in {wait}s.")
                sleep(wait)
                continue
        return value

    return wrapper_request


@dataclass
class PowerBIToken:
    client_id: str
    client_secret: str
    tenant_id: str = "7949eec9-bff5-4560-aa4a-fba8ab055d6c"
    resource_url: str = "https://analysis.windows.net/powerbi/api"
    get_token_method: REFRESH_TYPE = "oauth"
    authority_base_url: str = "https://login.microsoftonline.com/"
    username: str | None = None
    password: str | None = None
    scopes: list | None = None
    """Retrieve a PowerBI access token for use with the PowerBI API

    Args:
        client_id (str): The Application (client) ID of the application.
        client_secret (str): The client secret value of the application, generated in 'Certificates and Secrets'
        tenant_id (str, optional): The tenant id of application and Power BI. Defaults to "7949eec9-bff5-4560-aa4a-fba8ab055d6c".
        resource_url (_type_, optional): The resource url string. Defaults to "https://analysis.windows.net/powerbi/api".
        get_access_token (bool, optional): When set to true the class will return an access token on creation. If set to False no access token is returned on class initialisation and must be called with the get_access_token method. Defaults to True.
        get_token_method (refresh_type, optional): Can be either 'msal' or 'oath'. This defines the method used to retrieve the access token, msal will use the msal python package while oath will use simple requests. Defaults to "oauth".
    """

    def __post_init__(self):
        self.auth_tenant_url = f"{self.authority_base_url}{self.tenant_id}"
        self.token_details = None
        self.user_auth = True if self.username and self.password else False
        self._fetch_access_token(refresh_auth=self.get_token_method)

    def _fetch_access_token(
        self, refresh_auth: REFRESH_TYPE = "oauth", force_refresh: bool = False
    ) -> str:
        if self.token_details is not None and force_refresh is False:
            if self._token_expired() is False:
                return self.token_details
        if refresh_auth == "oauth":
            self.token_details = self._get_oauth_token()
        else:
            self.token_details = self._get_msal_token()
        if not self.token_details.get("access_token"):
            raise ValueError(
                f"Failed to retrieve PowerBI access token: {self.token_details}"
            )
        if not self.token_details.get("expires_on"):
            self.token_details["expires_on"] = int(time.time()) + int(
                self.token_details["expires_in"]
            )

    def get_access_token(self):
        self._fetch_access_token(self.get_token_method)
        if self.token_details.get("access_token"):
            return self.token_details["access_token"]

    def get_auth_header(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}",
        }

    def _get_oauth_token(self):
        import requests
        from urllib.parse import urlencode

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "resource": self.resource_url,
        }
        if self.user_auth:
            data | {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
        r = requests.post(
            url=f"{self.auth_tenant_url}/oauth2/token",
            data=urlencode(data).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return json.loads(r.text)

    def _get_msal_token(self):
        import msal

        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.auth_tenant_url,
            client_credential=self.client_secret,
        )
        if self.user_auth:
            return app.acquire_token_by_username_password(
                scopes=self.scopes, username=self.username, password=self.password
            )
        return app.acquire_token_for_client(scopes=[self.resource_url + "/.default"])

    def _token_expired(self) -> bool | None:
        if self.token_details:
            return float(self.token_details["expires_on"]) < (time.time() + 120)
        return None


@dataclass(kw_only=True)
class PowerBiAPI:
    token: PowerBIToken
    api_version: str = "v1.0"
    timeout: int = 3600
    poll_time: int = 30
    base_url: str = "https://api.powerbi.com"
    url: str = ""

    def __post_init__(self):
        self.url = self.get_url()
        self.refresh_id = None

    @request_retry
    def post_request(self, url: str, body={}):
        logging.info(f"POST: {url}")
        logging.info(f"Body: {body}")
        r = requests.post(url=url, headers=self.token.get_auth_header(), json=body)
        return self.parse_response(r)

    @request_retry
    def delete_request(self, url: str, body={}):
        r = requests.delete(url=url, headers=self.token.get_auth_header(), json=body)
        return self.parse_response(r)

    @request_retry
    def get_request(self, url):
        r = requests.get(url=url, headers=self.token.get_auth_header())
        if r.status_code == 405:
            return {}
        return self.parse_response(r)

    def parse_response(self, response: Response):
        logging.info(f"Response Status: {response.status_code}")
        response.raise_for_status()
        data = {}
        if response.text:
            data = response.json()
        self.request_id = response.headers.get("RequestId")
        return data["value"] if data.get("value") else data.get("results", data)

    def get_url(self):
        return f"{self.base_url}/{self.api_version}/myorg"

    def get_workspaces_url(self, workspace_id):
        return f"{self.url}/groups/{workspace_id}/datasets"

    def get_workspaces(self):
        return self.get_request(self.get_workspaces_url())


@dataclass(kw_only=True)
class PowerBiAPIWorkspace(PowerBiAPI):
    workspace_id: str | None = None
    workspace_env: Environment | None = None

    def __post_init__(self):
        super().__post_init__()
        self.workspace_env = (
            "dev"
            if self.workspace_id is None and self.workspace_env is None
            else self.workspace_env
        )
        self.workspace_id = (
            self.get_workspace_id() if self.workspace_id is None else self.workspace_id
        )

    def get_workspace_id(self):
        return WORKSPACE_IDS[self.workspace_env]

    def get_models(self):
        return self.get_request(f"{self.url}/groups/{self.workspace_id}/datasets")


@dataclass(kw_only=True)
class PowerBiAPIDataset(PowerBiAPI):
    dataset: str
    workspace_id: str | None = None
    workspace_env: Environment | None = None
    # table: str | list[str] | None = None
    # partition: str | list[str] | None = None
    table_partition: dict[List] | None = None
    dataset_id: str | None = None
    max_parallelism: int = 10
    commit_mode: Literal["transactional", "partialBatch"] = "transactional"

    status_list = ["Unknown", "Disabled", "Failed", "Completed"]

    def __post_init__(self):
        super().__post_init__()
        # self.table = [self.table] if isinstance(self.table, str) else self.table
        self.workspace_env = (
            "dev"
            if self.workspace_id is None and self.workspace_env is None
            else self.workspace_env
        )
        self.workspace_id = (
            self.get_workspace_id() if self.workspace_id is None else self.workspace_id
        )
        self.datasets_url = self.get_datasets_url()
        self.dataset_id = (
            self.get_dataset_id() if self.dataset_id is None else self.dataset_id
        )
        self.refresh_url = self.get_refresh_url()
        self.body_xmla = self.get_xmla_body()

    def get_workspace_id(self):
        return WORKSPACE_IDS[self.workspace_env]

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

    def execute_query(self, query: mspbi_xmla.PowerBIDaxQuery | dict):
        body = query if isinstance(query, dict) else query.to_dict()
        return self.post_request(url=self.get_exec_query_url(), body=body)

    def update_parameters(self, param_value: mspbi_xmla.PowerBIParameters | dict):
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
        xmla = mspbi_xmla.PowerBIRefreshPartition(
            datasets=[
                mspbi_xmla.PowerBIDataset(database=self.dataset, table=t, partition=p)
                for t, partitions in tbls_parts.items()
                for p in partitions
            ],
            commit_mode=self.commit_mode,
            max_parallelism=self.max_parallelism,
        ).to_dict()
        return xmla
