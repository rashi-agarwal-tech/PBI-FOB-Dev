from dotenv import load_dotenv
from pathlib import Path
import os

env_file = (Path(__file__).parent.parent / ".env").absolute()
load_dotenv(env_file)


def get_client_id():
    return os.getenv("client_id")


def get_client_secret() -> str:
    return os.getenv("client_secret")


def get_db_password():
    return os.getenv("db_password")


def get_db_username() -> str:
    return os.getenv("db_username")


def get_api_password():
    return os.getenv("api_password")


def get_api_username() -> str:
    return os.getenv("api_username")
