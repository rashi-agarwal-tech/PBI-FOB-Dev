from typing import Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests
from requests import Response
from pbi_tools.utils.constants import RETRY_LIST, ATTEMPTS, PBI_BASE_URL
import logging
from time import sleep
import functools
from pbi_tools.api.auth import MSAuthToken


def request_retry(func):
    @functools.wraps(func)
    def wrapper_request(*args, **kwargs):
        for i, wait in enumerate(RETRY_LIST):
            try:
                value = func(*args, **kwargs)
            except Exception as e:
                if i == ATTEMPTS - 1:
                    raise
                logging.warning(
                    f"\nError requesting PBI {e}\n{e.response.content}\nup for retry in {wait}s."
                )
                sleep(wait)
                continue
            break
        return value

    return wrapper_request


@dataclass(kw_only=True)
class MSApi(ABC):
    token: MSAuthToken
    api_version: str = "v1.0"
    timeout: int = 3600
    poll_time: int = 30
    base_url: str = PBI_BASE_URL
    url: str = ""

    def __post_init__(self):
        self.url = self.get_url()
        self.refresh_id = None

    @request_retry
    def post_request(self, url: str, body={}, parse_response: bool = True):
        headers = self.token.get_auth_header()
        print(f"POST: {url}")
        print(f"Body: {body}")
        r = requests.post(url=url, headers=headers, json=body)
        return self.parse_response(r) if parse_response else r

    @request_retry
    def delete_request(self, url: str, body={}, parse_response: bool = True):
        r = requests.delete(url=url, headers=self.token.get_auth_header(), json=body)
        return self.parse_response(r) if parse_response else r

    @request_retry
    def get_request(self, url: str, parse_response: bool = True) -> Any:
        r = requests.get(url=url, headers=self.token.get_auth_header())
        return self.parse_response(r) if parse_response else r

    @request_retry
    def save_request(self, url: str, filename: str) -> None:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f_out.write(chunk)
        return None

    @abstractmethod
    def parse_response(self, response: Response) -> Any:
        pass

    @abstractmethod
    def get_url(self):
        pass
