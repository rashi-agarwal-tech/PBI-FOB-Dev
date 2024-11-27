from pbi_tools.api.requester import MSApi
from dataclasses import dataclass
from requests import Response
from pbi_tools.utils.constants import FABRIC_BASE_URL, ENV
from pbi_tools.api.workspace import get_workspace_id
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Annotated, TypeAlias, Literal
from datetime import datetime
from pbi_tools.api.models import ExportStatus
from time import sleep


class ItemIdentifier(BaseModel):
    logicalId: str | None = None
    objectId: str | None = None


class ItemMetadata(BaseModel):
    itemIdentifier: ItemIdentifier
    itemType: str
    displayName: str


class ItemChange(BaseModel):
    itemMetadata: ItemMetadata
    remoteChange: str | None = None
    workspaceChange: str | None = None
    conflictType: str


class GitStatusResponse(BaseModel):
    workspaceHead: str
    remoteCommitHash: str
    changes: List[ItemChange | None]


conflictResolutionPolicy: TypeAlias = Literal["PreferWorkspace", "PreferRemote"]
CommitMode: TypeAlias = Literal["All", "Selective"]


class WorkspaceConflictResolution(BaseModel):
    conflictResolutionType: str = ("Workspace",)
    conflictResolutionPolicy: conflictResolutionPolicy


class UpdateOptions(BaseModel):
    allowOverrideItems: bool = True


class UpdateFromGitRequest(BaseModel):
    workspaceHead: str
    remoteCommitHash: str
    conflictResolution: WorkspaceConflictResolution
    options: UpdateOptions


class GitResponseHeader(BaseModel):
    location: Annotated[str, Field(alias="Location")]
    operation_id: Annotated[str, Field(alias="x-ms-operation-id")]
    retry_after: Annotated[str, Field(alias="Retry-After")]

    model_config = ConfigDict(extra="ignore")


class CommitToGitRequest(BaseModel):
    mode: CommitMode
    workspaceHead: str
    comment: str
    items: List[ItemIdentifier] | None = None


class ErrorRelatedResource(BaseModel):
    resourceId: str | None = None
    resourceType: str | None = None


class ErrorResponseDetails(BaseModel):
    errorCode: str
    message: str
    relatedResource: ErrorRelatedResource


class ErrorResponse(BaseModel):
    errorCode: str
    message: str
    moreDetails: ErrorResponseDetails
    relatedResource: ErrorRelatedResource
    requestId: str


class OperationStatus(BaseModel):
    status: str
    createdTimeUtc: datetime
    lastUpdatedTimeUtc: datetime
    percentComplete: int
    error: str | None = None


# Can we override workspace and use the workspace parsing?
@dataclass(kw_only=True)
class MSApiFabric(MSApi):
    workspace_id: str | None = None
    workspace_env: ENV | None = None

    def __post_init__(self):
        self.base_url = FABRIC_BASE_URL
        self.api_version = "v1"
        super().__post_init__()
        self.workspace_env, self.workspace_id = get_workspace_id(
            self.workspace_id, self.workspace_env
        )

    def parse_response(self, response: Response):
        response.raise_for_status()
        if response.status_code in (200, 201):
            return response.json()
        if response.status_code == 202:
            try:
                git_response_header = GitResponseHeader(**response.headers)
                return self.poll_operation(git_response_header.location)
            except Exception:
                return response.json()
        return response

    def get_url(self):
        return f"{self.base_url}/{self.api_version}"

    @property
    def get_git_url(self):
        return f"{self.url}/workspaces/{self.workspace_id}/git"

    def get_git_status(self) -> GitStatusResponse:
        print("Getting workspace sync status...")
        return GitStatusResponse(**self.get_request(f"{self.get_git_url}/status"))

    def update_workspace_from_git(self, git_sts: GitStatusResponse | None = None):
        if git_sts is None:
            git_sts = self.get_git_status()
        if not git_sts.changes or any(
            [c for c in git_sts.changes if c.conflictType != "None"]
        ):
            print(
                f"No changes to be synced from git {self.workspace_env} branch or conflicts exist"
            )
            return git_sts
        print(f"Updating {self.workspace_env} workspace changes from git")
        return self.post_request(
            f"{self.get_git_url}/updateFromGit",
            body=self.get_workspace_to_git_body(git_sts),
        )

    def commit_workspace_to_git(self, git_sts: GitStatusResponse | None = None):
        if git_sts is None:
            git_sts = self.get_git_status()
        if not git_sts.changes or any(
            [c for c in git_sts.changes if c.conflictType != "None"]
        ):
            print("No changes to be made or conflicts exist")
            return git_sts
        print(f"Committing {self.workspace_env} workspace changes to git")
        return self.post_request(
            f"{self.get_git_url}/commitToGit",
            body=self.get_workspace_to_git_body(git_sts),
        )

    def get_workspace_from_git_body(self, git_sts: GitStatusResponse | None = None):
        if git_sts is None:
            git_sts = self.get_git_status()
        return UpdateFromGitRequest(
            git_sts.workspaceHead,
            git_sts.remoteCommitHash,
            WorkspaceConflictResolution(conflictResolutionPolicy="PreferRemote"),
            UpdateOptions(),
        ).model_dump()

    def get_workspace_to_git_body(self, git_sts: GitStatusResponse | None = None):
        if git_sts is None:
            git_sts = self.get_git_status()
        if git_sts.changes:
            print(git_sts)
            changes_msg = "\n".split(
                [
                    f"{c.workspaceChange}:{c.itemMetadata.itemType}, {c.itemMetadata.displayName}"
                    for c in git_sts.changes
                ]
            )
            return CommitToGitRequest(
                mode="All",
                workspaceHead=git_sts.workspaceHead,
                comment=f"feat: synced changes from workspace\n\n{changes_msg}",
            ).model_dump()

    def sync_workspace_git(self):
        print(self.commit_workspace_to_git())
        return self.update_workspace_from_git()

    def poll_operation(self, operation_url: str):
        print("Polling for git sync status...")
        op_status = OperationStatus(**self.get_request(operation_url))
        print(op_status)
        while op_status.status != ExportStatus.SUCCEEDED:
            if op_status.status in (ExportStatus.FAILED, ExportStatus.UNDEFINED):
                raise Exception(f"Error polling for status: {op_status}")
            sleep(10)
            op_status = OperationStatus(**self.get_request(operation_url))
            print(op_status)
        return op_status
        # return self.get_request(f"{operation_url}/result")


if __name__ == "__main__":
    from pbi_tools.api.auth import get_user_token

    git_api = MSApiFabric(token=get_user_token(), workspace_env="uat")
    git_sts = git_api.get_git_status()
    print(git_sts)
    # out = git_api.commit_workspace_to_git()
    # print(out)
    # git_sts = git_api.get_git_status()
    # print(git_sts)
