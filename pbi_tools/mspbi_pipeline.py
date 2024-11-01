from pbi_tools.mspbi_api import PowerBIToken
from dataclasses import dataclass
import requests
from requests import Response
from pbi_tools import load_envs
from pbi_tools import constants

import logging

scopes = [
    "https://api.fabric.microsoft.com/Workspace.GitUpdate.All",
    "https://api.fabric.microsoft.com/Workspace.GitCommit.All",
]


@dataclass(kw_only=True)
class FabricAPI:
    token: PowerBIToken
    api_version: str = "v1"
    timeout: int = 3600
    poll_time: int = 30
    base_url: str = "https://api.fabric.microsoft.com"
    url: str = ""

    def __post_init__(self):
        self.url = self.get_url()
        self.refresh_id = None

    def post_request(self, url: str, body={}):
        logging.info(f"POST: {url}")
        logging.info(f"Body: {body}")
        r = requests.post(url=url, headers=self.token.get_auth_header(), json=body)
        return self.parse_response(r)

    def delete_request(self, url: str, body={}):
        r = requests.delete(url=url, headers=self.token.get_auth_header(), json=body)
        return self.parse_response(r)

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
        return f"{self.base_url}/{self.api_version}"

    def get_git_status(self, workspaceId):
        self.get_request(f"{self.url}/workspaces/{workspaceId}/git/status")


if __name__ == "__main__":
    token = PowerBIToken(
        client_id=load_envs.get_client_id(),
        client_secret=load_envs.get_client_secret(),
        resource_url="https://api.fabric.microsoft.com/",
        get_token_method="msal",
        username=load_envs.get_api_username(),
        password=load_envs.get_api_password(),
        scopes=scopes,
    )
    repsonse = FabricAPI(token=token).get_git_status(constants.WORKSPACE_IDS.get("dev"))
    print("response")
