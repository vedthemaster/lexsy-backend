import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv()


class BaseConfig(BaseSettings):
    class Config:
        case_sensitive = True


# Try to load from config.yml as fallback
config_file_path = os.path.join(os.getcwd(), "config", "config.yml")
set_yaml = None

if os.path.exists(config_file_path):
    with open(config_file_path, encoding="utf-8") as f:
        set_yaml = yaml.safe_load(f)


class Config(BaseConfig):
    # Database settings - prioritize environment variables
    DB_CONNECTION: str = os.getenv("MONGODB_URI") or (
        set_yaml["database"]["connection_string"] if set_yaml else ""
    )
    DB_NAME: str = os.getenv("MONGODB_NAME") or (
        set_yaml["database"]["name"] if set_yaml else "lexy"
    )

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or (
        set_yaml["openai"]["api_key"] if set_yaml else ""
    )
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL") or (
        set_yaml["openai"]["model"] if set_yaml else "gpt-4o-mini"
    )
    OPENAI_PARSER_ASSISTANT_ID: str = os.getenv("OPENAI_PARSER_ASSISTANT_ID") or (
        set_yaml["openai"]["parser_assistant_id"] if set_yaml else ""
    )
    OPENAI_FILLER_ASSISTANT_ID: str = os.getenv("OPENAI_FILLER_ASSISTANT_ID") or (
        set_yaml["openai"]["filler_assistant_id"] if set_yaml else ""
    )


config: Config = Config()
