from pydantic_settings import BaseSettings
import yaml


class BaseConfig(BaseSettings):
    class Config:
        case_sensitive = True


with open("config\config.yml", "r", encoding="utf-8") as f:
    set_yaml = yaml.safe_load(f)


class Config(BaseConfig):

    DB_CONNECTION: str = set_yaml["database"]["connection_string"]
    DB_NAME: str = set_yaml["database"]["name"]

    OPENAI_API_KEY: str = set_yaml["openai"]["api_key"]
    OPENAI_MODEL: str = set_yaml["openai"]["model"]
    OPENAI_ASSISTANT_ID: str = set_yaml["openai"]["assistant_id"]


config: Config = Config()
