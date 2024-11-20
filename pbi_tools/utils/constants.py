from typing import TypeAlias, Literal
from pathlib import Path

ATTEMPTS = 5
BACKOFF_FACTOR = 5
RETRY_LIST = [BACKOFF_FACTOR * (2 ** (a)) for a in range(ATTEMPTS)]

FISCAL_YEAR_START_MONTH = 4

PROJECT_DIR = Path(__file__).parent.parent.parent
PBI_DIR = PROJECT_DIR / "powerbi"
PARTITIONS_DIR = PBI_DIR / "partitions"
REPORT_DIR = PBI_DIR / "workspaces"

PBI_META_DIR = PROJECT_DIR / "pbi_tools" / "partitions"
PBI_META_FILE = PBI_META_DIR / "model_tables.json"

WORKSPACE_ENVS = {
    "dev": "D&A Dev - Dr. Martens Datasets",
    "uat": "D&A UAT - Dr. Martens Datasets",
    "prod": "Dr. Martens Datasets",
}

WORKSPACE_IDS = {
    "dev": "e8649e55-b7f9-42aa-91f7-326ed4c8a36d",
    "uat": "1c9ba3dd-9e1d-474b-94ca-9d8d844e656b",
    "prod": "c0d45d23-3054-4aea-b360-e68dd9d877c9",
}

SF_ENVS = {
    "dev": "drmartensdev.west-europe.azure.snowflakecomputing.com",
    "uat": "drmartensuat.west-europe.azure.snowflakecomputing.com",
    "prod": "drmartensprod.west-europe.azure.snowflakecomputing.com",
}

PBI_STATUS_LIST = ["Unknown", "Disabled", "Failed", "Completed"]

PBI_STATUS_MAP = {
    "Unknown": "In Progress",
    "Disabled": "Disabled",
    "Failed": "Failed",
    "Completed": "Completed",
    "Cancelled": "Cancelled",
    "InProgress": "In Progress",
}

PBI_BASE_URL: str = "https://api.powerbi.com"

REFRESH_TYPE: TypeAlias = Literal["msal", "oauth"]
ENV: TypeAlias = Literal["dev", "uat", "prod"]

TENANT_ID: str = "7949eec9-bff5-4560-aa4a-fba8ab055d6c"
PBI_RESOURCE_URL: str = "https://analysis.windows.net/powerbi/api"
AUTHORITY_BASE_URL: str = "https://login.microsoftonline.com/"
FABRIC_BASE_URL: str = "https://api.fabric.microsoft.com"

if __name__ == "__main__":
    print(f"Here you go: {PROJECT_DIR}")
