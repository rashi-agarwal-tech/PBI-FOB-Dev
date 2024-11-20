from typing import List
from dataclasses import dataclass
from requests import Response
from pbi_tools.utils.constants import *
import logging
from pbi_tools.api.models import PowerBIReport
from pbi_tools.api.requester import MSApi


def get_workspace_id(
    workspace_id: str | None = None, workspace_env: ENV | None = None
) -> ENV:
    workspace_env = (
        "dev" if workspace_id is None and workspace_env is None else workspace_env
    )
    workspace_id = (
        WORKSPACE_IDS[workspace_env] if workspace_id is None else workspace_id
    )
    return workspace_env, workspace_id


@dataclass(kw_only=True)
class MSApiWorkspace(MSApi):
    workspace_id: str | None = None
    workspace_env: ENV | None = None

    def __post_init__(self):
        super().__post_init__()
        self.workspace_env, self.workspace_id = get_workspace_id(
            self.workspace_id, self.workspace_env
        )

    def get_workspace_url(self):
        return f"{self.url}/groups/{self.workspace_id}"

    def get_workspace_datasets(self):
        return self.get_request(self.get_workspace_datasets_url())

    def get_workspace_reports(self) -> List[PowerBIReport]:
        response = self.get_request(self.get_workspace_reports_url())
        return [PowerBIReport(**pbi_report) for pbi_report in response]

    def get_workspace_reports_url(self) -> str:
        return f"{self.get_workspace_url()}/reports"

    def get_workspace_datasets_url(self) -> str:
        return f"{self.get_workspace_url()}/datasets"

    # Overridden from MSApi
    def get_url(self):
        return f"{self.base_url}/{self.api_version}/myorg"

    # Overridden from MSApi
    def parse_response(self, response: Response):
        logging.info(f"Response Status: {response.status_code}")
        # I don't recall why I am ignoring 405s? MJK.
        if response.status_code == 405:
            return {}
        response.raise_for_status()
        data = {}
        if response.text:
            data = response.json()
        self.request_id = response.headers.get("RequestId")
        return data["value"] if data.get("value") else data.get("results", data)
