from __future__ import annotations

from pbi_tools.api.auth import MSAuthToken
from pbi_tools.api.workspace import MSApiWorkspace
from dataclasses import dataclass
from pbi_tools.utils import load_envs
from time import sleep
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Annotated
from pbi_tools.api.models import ExportStatus

# POST https://api.powerbi.com/v1.0/myorg/groups/e8649e55-b7f9-42aa-91f7-326ed4c8a36d/reports/18b94d00-0fa7-4e6d-a3ab-e7582cad23f7/ExportTo
# Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6IjNQYUs0RWZ5Qk5RdTNDdGpZc2EzWW1oUTVFMCIsImtpZCI6IjNQYUs0RWZ5Qk5RdTNDdGpZc2EzWW1oUTVFMCJ9.eyJhdWQiOiJodHRwczovL2FuYWx5c2lzLndpbmRvd3MubmV0L3Bvd2VyYmkvYXBpIiwiaXNzIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNzk0OWVlYzktYmZmNS00NTYwLWFhNGEtZmJhOGFiMDU1ZDZjLyIsImlhdCI6MTczMDk3OTg3MSwibmJmIjoxNzMwOTc5ODcxLCJleHAiOjE3MzA5ODQ0NzQsImFjY3QiOjAsImFjciI6IjEiLCJhaW8iOiJBVlFBcS84WUFBQUEzeTExVy9GWnpBMjNPMWJ1M2ZKQnlTVzdmSDFFSVhjSFREY3lQaUdBL1YxelR2T2dVUnZWb1l1T2dLRlhKNTcxR3o4Q3E3ck5QL1JsWk5vYnJzMzFIdmN0QkttbFFXNHpTL2R2Q2ttaFMyaz0iLCJhbXIiOlsicHdkIiwicnNhIiwibWZhIl0sImFwcGlkIjoiMThmYmNhMTYtMjIyNC00NWY2LTg1YjAtZjdiZjJiMzliM2YzIiwiYXBwaWRhY3IiOiIwIiwiZGV2aWNlaWQiOiI1MjZiOGFhZi00ZWM3LTRlMGYtYTUyMi0xNWY3ZTIwNGVmZTEiLCJmYW1pbHlfbmFtZSI6IlNWQyIsImdpdmVuX25hbWUiOiJQb3dlckJJU0EiLCJpZHR5cCI6InVzZXIiLCJpcGFkZHIiOiI4My42Ny4yMzguMCIsIm5hbWUiOiJQb3dlckJJU0EtU1ZDIiwib2lkIjoiMWQ3Mjk5NTEtYTcxZC00NGRiLWE2ZDEtYTQwMWU1YzU0MTg0IiwicHVpZCI6IjEwMDMyMDAyNTQ0QUYwRDYiLCJyaCI6IjEuQVhRQXllNUplZldfWUVXcVN2dW9xd1ZkYkFrQUFBQUFBQUFBd0FBQUFBQUFBQUIwQUJwMEFBLiIsInNjcCI6IkFwcC5SZWFkLkFsbCBDYXBhY2l0eS5SZWFkLkFsbCBDYXBhY2l0eS5SZWFkV3JpdGUuQWxsIENvbm5lY3Rpb24uUmVhZC5BbGwgQ29ubmVjdGlvbi5SZWFkV3JpdGUuQWxsIENvbnRlbnQuQ3JlYXRlIERhc2hib2FyZC5SZWFkLkFsbCBEYXNoYm9hcmQuUmVhZFdyaXRlLkFsbCBEYXRhZmxvdy5SZWFkLkFsbCBEYXRhZmxvdy5SZWFkV3JpdGUuQWxsIERhdGFzZXQuUmVhZC5BbGwgRGF0YXNldC5SZWFkV3JpdGUuQWxsIEdhdGV3YXkuUmVhZC5BbGwgR2F0ZXdheS5SZWFkV3JpdGUuQWxsIEl0ZW0uRXhlY3V0ZS5BbGwgSXRlbS5FeHRlcm5hbERhdGFTaGFyZS5BbGwgSXRlbS5SZWFkV3JpdGUuQWxsIEl0ZW0uUmVzaGFyZS5BbGwgT25lTGFrZS5SZWFkLkFsbCBPbmVMYWtlLlJlYWRXcml0ZS5BbGwgUGlwZWxpbmUuRGVwbG95IFBpcGVsaW5lLlJlYWQuQWxsIFBpcGVsaW5lLlJlYWRXcml0ZS5BbGwgUmVwb3J0LlJlYWRXcml0ZS5BbGwgUmVwcnQuUmVhZC5BbGwgU3RvcmFnZUFjY291bnQuUmVhZC5BbGwgU3RvcmFnZUFjY291bnQuUmVhZFdyaXRlLkFsbCBUZW5hbnQuUmVhZC5BbGwgVGVuYW50LlJlYWRXcml0ZS5BbGwgVXNlclN0YXRlLlJlYWRXcml0ZS5BbGwgV29ya3NwYWNlLkdpdENvbW1pdC5BbGwgV29ya3NwYWNlLkdpdFVwZGF0ZS5BbGwgV29ya3NwYWNlLlJlYWQuQWxsIFdvcmtzcGFjZS5SZWFkV3JpdGUuQWxsIiwic2lnbmluX3N0YXRlIjpbImR2Y19tbmdkIiwiZHZjX2NtcCIsImttc2kiXSwic3ViIjoielRacURWOEUxOUl2UElFSGtOenpTR2VLYmI0a1RiNVJsb2JJNmxmYThKYyIsInRpZCI6Ijc5NDllZWM5LWJmZjUtNDU2MC1hYTRhLWZiYThhYjA1NWQ2YyIsInVuaXF1ZV9uYW1lIjoiUG93ZXJCSVNBLVNWQ0Bkcm1hcnRlbnMuY29tIiwidXBuIjoiUG93ZXJCSVNBLVNWQ0Bkcm1hcnRlbnMuY29tIiwidXRpIjoiMkFrVkMwYmEyRTJ4eW1lUmV0ektBQSIsInZlciI6IjEuMCIsIndpZHMiOlsiYTllYTg5OTYtMTIyZi00Yzc0LTk1MjAtOGVkY2QxOTI4MjZjIiwiYjc5ZmJmNGQtM2VmOS00Njg5LTgxNDMtNzZiMTk0ZTg1NTA5Il0sInhtc19pZHJlbCI6IjEgNiJ9.VevgQyig5sm7Sx3xE1UwB2aj-XTLvN_rzh0bR9Om-pqdTBy88lyJcCv8zirnz2JiZMdlAbr39g8bfWIs0Ef8mzFybKlt1EclF8_p6yDrP9PQZxqdsReEN401EIcRbAjITTE2Q-AIHErThLd4RdbGjExshhTA4t56thLSTl9Gy_iOqSSatCaXFrotDDnb0wMB2sPXpo-hBqHzMS0xhEF3RtQGkNaD9GUH183HHUooQsyl3UgrPVmbIyxpiatNzxn7xBHJt1umi4yvLxeG1Iauq1n_0BnjRfwx-rAWn0GWXOU9SYohQGlH3ZuDcRk4iXZTKLrLW1QJpF29c0GH6Osm2g
# Content-type: application/json

fixed_assests_report_id = "18b94d00-0fa7-4e6d-a3ab-e7582cad23f7"


class ExportEntity(BaseModel):
    odata_context: Annotated[HttpUrl | None, Field(alias="@odata.context")] = None
    id: str
    createdDateTime: datetime
    lastActionDateTime: datetime
    reportId: str
    reportName: str | None = None
    status: str
    percentComplete: int
    resourceLocation: HttpUrl | None = None
    resourceFileExtension: str | None = None
    expirationTime: datetime


@dataclass(kw_only=True)
class MSApiReport(MSApiWorkspace):
    report_id: str | None = None
    report_name: str | None = None

    def __post_init__(self):
        super().__post_init__()
        self.report_id = (
            self.get_report_id() if self.report_id is None else self.report_id
        )

    # We only appear to get one data set (the environment one), also should add all properties or not required
    # Can I just use all datasets in all three workspaces?
    def get_report_id(self):
        if self.report_name is None:
            raise ValueError("You must supply either a report_id or a report_name")
        reports = self.get_workspace_reports()
        report_ids = [
            pbi_report for pbi_report in reports if self.report_name == pbi_report.name
        ]
        if not report_ids:
            raise ValueError(
                f"Report Name: {self.report_name} not found in workspace {self.workspace_id}"
            )
        if len(report_ids) > 1:
            raise ValueError(
                f"Multiple report found, please use ID instead: {report_ids}"
            )
        return report_ids[0].id

    def get_reports_url(self):
        return f"{self.get_workspace_url()}/reports/{self.report_id}"

    def get_report_datasources(self):
        return self.get_request(f"{self.get_reports_url()}/datasources")

    def get_export_status(self, export_id: str) -> ExportEntity:
        status = self.get_request(url=f"{self.get_reports_url()}/exports/{export_id}")
        return ExportEntity(**status)

    def export_report(self, format: str):
        # get list of data sets from report... api call
        # GET https://api.powerbi.com/v1.0/myorg/groups/{groupId}/reports/{reportId}/datasources

        body = {
            "powerBIReportConfiguration": {
                "identities": [
                    {
                        "username": "PowerBISA-SVC@drmartens.com",
                        "roles": ["Dataset.Read.All", "Report.ReadWrite.All"],
                        "datasets": [
                            "61d8dabc-28c0-4096-a406-2bd0d7e4fb97",
                            "58323929-f26d-42de-9f21-efb7542913eb",
                            "c7801869-9109-4f91-9cb7-b5d465162fb0",
                        ],
                    }
                ]
            },
            "format": format,
        }
        export = ExportEntity(
            **self.post_request(url=f"{self.get_reports_url()}/ExportTo", body=body)
        )
        while export.status != ExportStatus.SUCCEEDED:
            sleep(10)
            export = self.get_export_status(export.id)
            print(
                f"Exporting report {self.report_name}, {export.status}: {export.percentComplete}"
            )
            if export.status in (ExportStatus.FAILED, ExportStatus.UNDEFINED):
                raise Exception(f"Error saving report {self.report_name}")
        self.save_request(
            url=f"{self.get_reports_url()}/exports/{export.id}/file",
            filename=f"{export.reportName}.{export.resourceFileExtension}",
        )


# https://api.powerbi.com/v1.0/myorg/groups/e8649e55-b7f9-42aa-91f7-326ed4c8a36d/reports/18b94d00-0fa7-4e6d-a3ab-e7582cad23f7/exports/MS9CbG9iSWRWMi1kNzY4OGJhNC02ZGI3LTQyOWQtOTg3OS0xZDFjNDYwMWEyMTRnZWhJNEd3aVZ4UjJvNG1ONjJuMkJTQVh2THYxLg==/file')
# https://api.powerbi.com/v1.0/myorg/groups/e8649e55-b7f9-42aa-91f7-326ed4c8a36d/reports/18b94d00-0fa7-4e6d-a3ab-e7582cad23f7/exports/MS9CbG9iSWRWMi1kNzY4OGJhNC02ZGI3LTQyOWQtOTg3OS0xZDFjNDYwMWEyMTRnZWhJNEd3aVZ4UjJvNG1ONjJuMkJTQVh2THYxLg==/file

if __name__ == "__main__":
    token = MSAuthToken(
        client_id=load_envs.get_client_id(),
        client_secret=load_envs.get_client_secret(),
        get_token_method="msal",
    )

    repsonse = MSApiReport(
        token=token,
        workspace_env="dev",
        report_name="DMA Fixed Asset Regression",
    ).export_report("PDF")
    print(repsonse)
