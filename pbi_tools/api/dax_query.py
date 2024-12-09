from pbi_tools.api.requester import MSApi
from dataclasses import dataclass
from requests import Response
from pydantic import BaseModel
from typing import List


class Query(BaseModel):
    query: str


class SerializerSettings(BaseModel):
    includeNulls: bool


class InputModel(BaseModel):
    queries: List[Query]
    serializerSettings: SerializerSettings | None = None
    impersonatedUserName: str | None = None


@dataclass(kw_only=True)
class MSApiQuery(MSApi):
    def __post_init__(self):
        super().__post_init__()

    def parse_response(self, response: Response):
        response.raise_for_status()
        if response.status_code in (200, 201):
            return response.json()
        return response

    def get_url(self):
        return f"{self.base_url}/{self.api_version}/myorg/datasets"

    def execute_query(self, dataset_id: str, query: str):
        body = InputModel(
            queries=[Query(query=query)],
            serializerSettings=SerializerSettings(includeNulls=True),
        ).model_dump(exclude_none=True)
        return self.post_request(
            url=f"{self.get_url()}/{dataset_id}/executeQueries", body=body
        )


if __name__ == "__main__":
    pass
