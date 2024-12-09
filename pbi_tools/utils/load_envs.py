from dotenv import load_dotenv
from pathlib import Path
import os

env_file = (Path(__file__).parent.parent / ".env").absolute()
load_dotenv(env_file)

print(Path(__file__).parent.parent)


def get_client_id():
    return os.getenv("CLIENT_ID")


def get_client_secret() -> str:
    return os.getenv("CLIENT_SECRET")


def get_db_password():
    return os.getenv("DB_PASSWORD")


def get_db_username() -> str:
    return os.getenv("DB_USERNAME")


def get_api_password():
    return os.getenv("API_PASSWORD")


def get_api_username() -> str:
    return os.getenv("API_USERNAME")
