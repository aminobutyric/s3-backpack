"""
App configuration, loaded from environment variables (see .env.example).
"""

from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Garage / S3-compatible backend (only backend in v1 — cloud S3 is v1.1)
    s3_endpoint_url: str = "http://localhost:3900"
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "default-bucket"
    s3_region: str = "garage"

    # App auth — protects this app's own API, separate from the S3
    # credentials above. Required, not optional, even for single-user use.
    api_key: str

    model_config = ConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
