import pytest
from fastapi import HTTPException

from app.auth.api_key import is_valid_api_key
from app.auth.dependencies import require_api_key
from app.config import Settings


def test_is_valid_api_key() -> None:
    assert is_valid_api_key("secret", "secret")
    assert not is_valid_api_key("wrong", "secret")
    assert not is_valid_api_key(None, "secret")


def test_require_api_key_rejects_missing_key() -> None:
    settings = Settings(
        s3_access_key="access",
        s3_secret_key="secret",
        api_key="expected",
    )

    with pytest.raises(HTTPException) as exc:
        require_api_key(api_key=None, settings=settings)

    assert exc.value.status_code == 401


def test_require_api_key_accepts_matching_key() -> None:
    settings = Settings(
        s3_access_key="access",
        s3_secret_key="secret",
        api_key="expected",
    )

    assert require_api_key(api_key="expected", settings=settings) is None
