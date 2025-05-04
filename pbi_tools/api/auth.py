import json
from typing import Optional, Dict, Any
import time
from dataclasses import dataclass
from pbi_tools.utils.constants import (
    REFRESH_TYPE,
    FABRIC_BASE_URL,
    TENANT_ID,
    PBI_RESOURCE_URL,
    AUTHORITY_BASE_URL,
)


@dataclass
class MSAuthToken:
    client_id: str
    client_secret: str
    tenant_id: str = TENANT_ID
    resource_url: str = PBI_RESOURCE_URL
    get_token_method: REFRESH_TYPE = "oauth"
    authority_base_url: str = AUTHORITY_BASE_URL
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
        self.auth_tenant_url: str = f"{self.authority_base_url}{self.tenant_id}"
        self.token_details: Optional[Dict[Any, Any]] = None
        self.user_auth = True if self.username and self.password else False
        self._fetch_access_token(refresh_auth=self.get_token_method)

    def _fetch_access_token(
        self, refresh_auth: REFRESH_TYPE = "oauth", force_refresh: bool = False
    ) -> None:
        if self.token_details is not None and force_refresh is False:
            if self._token_expired() is False:
                return None 
        if refresh_auth == "oauth":
            self.token_details = self._get_oauth_token()
        else:
            self.token_details = self._get_msal_token()
        if self.token_details is not None and not self.token_details.get("access_token"):
            raise ValueError(
                f"Failed to retrieve PowerBI access token: {self.token_details}"
            )
        if self.token_details is not None and not self.token_details.get("expires_on"):
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
            # "Accept": None,
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
        return app.acquire_token_for_client(
            scopes=[
                self.resource_url + "/.default",
                # "https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All",
                # "https://analysis.windows.net/powerbi/api/Report.ReadWrite.All",
            ]
        )

    def _token_expired(self) -> bool | None:
        if self.token_details:
            return float(self.token_details["expires_on"]) < (time.time() + 120)
        return None


def get_token() -> MSAuthToken:
    from pbi_tools.utils import load_envs

    return MSAuthToken(
        client_id=load_envs.get_client_id(),
        client_secret=load_envs.get_client_secret(),
        get_token_method="msal",
    )


def get_user_token() -> MSAuthToken:
    from pbi_tools.utils import load_envs

    scopes = [
        "https://api.fabric.microsoft.com/Workspace.GitUpdate.All",
        "https://api.fabric.microsoft.com/Workspace.GitCommit.All",
    ]

    return MSAuthToken(
        client_id=load_envs.get_client_id(),
        client_secret=load_envs.get_client_secret(),
        resource_url=FABRIC_BASE_URL,
        get_token_method="msal",
        username=load_envs.get_api_username(),
        password=load_envs.get_api_password(),
        scopes=scopes,
    )
