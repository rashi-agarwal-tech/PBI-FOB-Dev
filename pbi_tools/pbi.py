from pbi_tools.api.auth import get_token
from pbi_tools.api.dataset import MSApiDataset

def validate_parameters(dataset: str, env: str = "dev") -> str:
    refresh_api = MSApiDataset(token=get_token(), dataset=dataset, workspace_env=env)
    params = refresh_api.get_parameters()
    vars = { var["name"]:var["currentValue"] for var in params }
    if (num_rows := vars.get("NumberOfRows", "0")) != "0":
        raise ValueError(f"NumberOfRow is not set to zero: {num_rows}")
    if (sn_server := vars.get("Datasource_Server", "")) != SF_ENVS[env]:
        raise ValueError(f"Datasource_Server is not set correctly for {env}: {sn_server}")
    return f"Parameters correctly set for the {env}:\n{params}"