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

# TODO: Finish Reports to allow saving of reports for the regression tools
# WARNING: This module is untested!

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
