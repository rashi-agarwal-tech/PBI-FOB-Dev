from pydantic import BaseModel, HttpUrl
from typing import List
from uuid import UUID
from enum import Enum


class PowerBIReport(BaseModel):
    id: UUID
    reportType: str
    name: str
    webUrl: HttpUrl
    embedUrl: HttpUrl
    isFromPbix: bool
    isOwnedByMe: bool
    datasetId: UUID
    datasetWorkspaceId: UUID
    users: List
    subscriptions: List
    sections: List


class ExportStatus(Enum):
    FAILED = "Failed"
    NOT_STARTED = "NotStarted"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    UNDEFINED = "Undefined"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)
