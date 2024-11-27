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
        # print(f"Body: {body}")
        # # headers = headers | {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IjNQYUs0RWZ5Qk5RdTNDdGpZc2EzWW1oUTVFMCIsImtpZCI6IjNQYUs0RWZ5Qk5RdTNDdGpZc2EzWW1oUTVFMCJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNzk0OWVlYzktYmZmNS00NTYwLWFhNGEtZmJhOGFiMDU1ZDZjLyIsImlhdCI6MTczMDk3OTg3MSwibmJmIjoxNzMwOTc5ODcxLCJleHAiOjE3MzA5ODQ0NzQsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBVlFBcS84WUFBQUEzeTExVy9GWnpBMjNPMWJ1M2ZKQnlTVzdmSDFFSVhjSFREY3lQaUdBL1YxelR2T2dVUnZWb1l1T2dLRlhKNTcxR3o4Q3E3ck5QL1JsWk5vYnJzMzFIdmN0QkttbFFXNHpTL2R2Q2ttaFMyaz0iLCJhbXIiOlsicHdkIiwicnNhIiwibWZhIl0sImFwcGlkIjoiMThmYmNhMTYtMjIyNC00NWY2LTg1YjAtZjdiZjJiMzliM2YzIiwiYXBwaWRhY3IiOiIwIiwiZGV2aWNlaWQiOiI1MjZiOGFhZi00ZWM3LTRlMGYtYTUyMi0xNWY3ZTIwNGVmZTEiLCJmYW1pbHlfbmFtZSI6IlNWQyIsImdpdmVuX25hbWUiOiJQb3dlckJJU0EiLCJpZHR5cCI6InVzZXIiLCJpcGFkZHIiOiI4My42Ny4yMzguMCIsIm5hbWUiOiJQb3dlckJJU0EtU1ZDIiwib2lkIjoiMWQ3Mjk5NTEtYTcxZC00NGRiLWE2ZDEtYTQwMWU1YzU0MTg0IiwicHVpZCI6IjEwMDMyMDAyNTQ0QUYwRDYiLCJyaCI6IjEuQVhRQXllNUplZldfWUVXcVN2dW9xd1ZkYkFrQUFBQUFBQUFBd0FBQUFBQUFBQUIwQUJwMEFBLiIsInNjcCI6IkFwcC5SZWFkLkFsbCBDYXBhY2l0eS5SZWFkLkFsbCBDYXBhY2l0eS5SZWFkV3JpdGUuQWxsIENvbm5lY3Rpb24uUmVhZC5BbGwgQ29ubmVjdGlvbi5SZWFkV3JpdGUuQWxsIENvbnRlbnQuQ3JlYXRlIERhc2hib2FyZC5SZWFkLkFsbCBEYXNoYm9hcmQuUmVhZFdyaXRlLkFsbCBEYXRhZmxvdy5SZWFkLkFsbCBEYXRhZmxvdy5SZWFkV3JpdGUuQWxsIERhdGFzZXQuUmVhZC5BbGwgRGF0YXNldC5SZWFkV3JpdGUuQWxsIEdhdGV3YXkuUmVhZC5BbGwgR2F0ZXdheS5SZWFkV3JpdGUuQWxsIEl0ZW0uRXhlY3V0ZS5BbGwgSXRlbS5FeHRlcm5hbERhdGFTaGFyZS5BbGwgSXRlbS5SZWFkV3JpdGUuQWxsIEl0ZW0uUmVzaGFyZS5BbGwgT25lTGFrZS5SZWFkLkFsbCBPbmVMYWtlLlJlYWRXcml0ZS5BbGwgUGlwZWxpbmUuRGVwbG95IFBpcGVsaW5lLlJlYWQuQWxsIFBpcGVsaW5lLlJlYWRXcml0ZS5BbGwgUmVwb3J0LlJlYWRXcml0ZS5BbGwgUmVwcnQuUmVhZC5BbGwgU3RvcmFnZUFjY291bnQuUmVhZC5BbGwgU3RvcmFnZUFjY291bnQuUmVhZFdyaXRlLkFsbCBUZW5hbnQuUmVhZC5BbGwgVGVuYW50LlJlYWRXcml0ZS5BbGwgVXNlclN0YXRlLlJlYWRXcml0ZS5BbGwgV29ya3NwYWNlLkdpdENvbW1pdC5BbGwgV29ya3NwYWNlLkdpdFVwZGF0ZS5BbGwgV29ya3NwYWNlLlJlYWQuQWxsIFdvcmtzcGFjZS5SZWFkV3JpdGUuQWxsIiwic2lnbmluX3N0YXRlIjpbImR2Y19tbmdkIiwiZHZjX2NtcCIsImttc2kiXSwic3ViIjoielRacURWOEUxOUl2UElFSGtOenpTR2VLYmI0a1RiNVJsb2JJNmxmYThKYyIsInRpZCI6Ijc5NDllZWM5LWJmZjUtNDU2MC1hYTRhLWZiYThhYjA1NWQ2YyIsInVuaXF1ZV9uYW1lIjoiUG93ZXJCSVNBLVNWQ0Bkcm1hcnRlbnMuY29tIiwidXBuIjoiUG93ZXJCSVNBLVNWQ0Bkcm1hcnRlbnMuY29tIiwidXRpIjoiMkFrVkMwYmEyRTJ4eW1lUmV0ektBQSIsInZlciI6IjEuMCIsIndpZHMiOlsiYTllYTg5OTYtMTIyZi00Yzc0LTk1MjAtOGVkY2QxOTI4MjZjIiwiYjc5ZmJmNGQtM2VmOS00Njg5LTgxNDMtNzZiMTk0ZTg1NTA5Il0sInhtc19pZHJlbCI6IjEgNiJ9.VevgQyig5sm7Sx3xE1UwB2aj-XTLvN_rzh0bR9Om-pqdTBy88lyJcCv8zirnz2JiZMdlAbr39g8bfWIs0Ef8mzFybKlt1EclF8_p6yDrP9PQZxqdsReEN401EIcRbAjITTE2Q-AIHErThLd4RdbGjExshhTA4t56thLSTl9Gy_iOqSSatCaXFrotDDnb0wMB2sPXpo-hBqHzMS0xhEF3RtQGkNaD9GUH183HHUooQsyl3UgrPVmbIyxpiatNzxn7xBHJt1umi4yvLxeG1Iauq1n_0BnjRfwx-rAWn0GWXOU9SYohQGlH3ZuDcRk4iXZTKLrLW1QJpF29c0GH6Osm2g"}
        # print(f"Headers: {headers}")
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
