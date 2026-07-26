"""
App configuration, loaded from environment variables (see .env.example).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Garage is the local S3 target used by the object browser and mirror jobs.
    s3_endpoint_url: str = "http://localhost:3900"
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "default-bucket"
    s3_region: str = "garage"

    # App auth — protects this app's own API, separate from the S3
    # credentials above. Required, not optional, even for single-user use.
    api_key: str

    # Rclone remotes are configured separately. The application passes only
    # named remote paths to rclone and never interpolates a shell command.
    rclone_binary: str = "rclone"
    rclone_config_path: str | None = None

    # Read-only Linux block-device inventory. Mounting and formatting are
    # intentionally outside this adapter.
    lsblk_binary: str = "lsblk"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    # Required values are supplied by the environment at runtime.
    return Settings()  # type: ignore[call-arg]
