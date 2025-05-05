from pbi_tools.partitions.partition_utils import pad_str_integer
from pbi_tools.api.auth import get_token, get_user_token
from pbi_tools.api import git
from pbi_tools.api.dataset import MSApiDataset
import pytest
from pbi_tools.cli import app
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.api
@pytest.mark.cli
def test_cli():
    result = runner.invoke(app, ["status", "--dataset", "DMA D2C", "--no-print-as-table"])
    assert result.exit_code == 0
    assert "DMA D2C" in result.stdout 


def test_pad_integer():
    pi_test1 = pad_str_integer("1")
    assert pi_test1 == "01"
    pi_test1 = pad_str_integer("7")
    assert pi_test1 == "07"
    pi_test1 = pad_str_integer("11")
    assert pi_test1 == "11"
    pi_test1 = pad_str_integer("111")
    assert pi_test1 == "111"


@pytest.mark.api
def test_auth():
    token = get_token()
    bearer = token.token_details.get("access_token")
    assert token is not None
    assert bearer is not None


@pytest.mark.api
# @pytest.mark.depends(on=['test_auth'])
def test_git_api():
    response = git.MSApiFabric(
        token=get_user_token(), workspace_env="dev"
    ).get_git_status()
    assert response.workspaceHead is not None
    assert response.remoteCommitHash is not None


# @pytest.mark.api
# # @pytest.mark.depends(on=['test_auth'])
# def test_report_api():
#     report = MSApiReport(
#         token=get_user_token(),
#         workspace_env="dev",
#         report_name="DMA Fixed Asset Regression",
#     )
#     assert report.report_id is not None
#     assert report.get_reports_url() is not None


@pytest.mark.api
# @pytest.mark.depends(on=['test_auth'])
def test_dataset_api():
    dataset = MSApiDataset(
        token=get_user_token(), workspace_env="dev", dataset="DMA D2C"
    )
    assert dataset.get_refresh_status() is not None


@pytest.mark.cli
def test_swap_partitions():
    result = runner.invoke(app, ["swap-partitions"])
    assert result.exit_code == 0

pytest.mark.api
# @pytest.mark.depends(on=['test_auth'])
def test_dataset_param_api():
    dataset = MSApiDataset(
        token=get_user_token(), workspace_env="dev", dataset="DMA D2C"
    )
    params = dataset.get_parameters()
    assert params is not None
