import os

import pytest

from app.config.maker import MakerConfig


def test_maker_config_from_env_success():
    """Test successful MakerConfig creation from environment variables."""
    # Setup test environment
    os.environ["MAKER_SESS_ID"] = "test_maker_id"
    os.environ["MAKER_SESS_AUTH"] = "4aa0e0f2-50eb-48a0-b78e-b6bb446ccd7b"
    os.environ["SIGNER_PRIV_KEY"] = (
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    )

    # Create config
    config = MakerConfig.from_env()

    # Assert values
    assert config.maker == "test_maker_id"
    assert config.authorization == "4aa0e0f2-50eb-48a0-b78e-b6bb446ccd7b"
    assert (
        config.signer_priv_key
        == "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    )


def test_maker_config_missing_maker_id():
    """Test MakerConfig creation fails when MAKER_SESS_ID is missing."""
    # Clear environment variables
    os.environ.pop("MAKER_SESS_ID", None)

    with pytest.raises(ValueError) as exc_info:
        MakerConfig.from_env()

    assert str(exc_info.value) == "MAKER_SESS_ID env var is not set"


def test_maker_config_non_uuid_auth():
    """Test MakerConfig creation fails when MAKER_SESS_AUTH is not UUID."""
    # Setup partial environment
    os.environ["MAKER_SESS_ID"] = "test_maker_id"
    os.environ["MAKER_SESS_AUTH"] = "bad-uuid-4aa0e0f2-50eb-48a0-b78e-b6bb446ccd7b-bad-uuid"

    with pytest.raises(ValueError) as exc_info:
        MakerConfig.from_env()

    assert "MAKER_SESS_AUTH must be a valid UUID" in str(exc_info.value)


def test_maker_config_missing_auth():
    """Test MakerConfig creation fails when MAKER_SESS_AUTH is missing."""
    # Setup partial environment
    os.environ["MAKER_SESS_ID"] = "test_maker_id"
    os.environ.pop("MAKER_SESS_AUTH", None)

    with pytest.raises(ValueError) as exc_info:
        MakerConfig.from_env()

    assert str(exc_info.value) == "MAKER_SESS_AUTH env var is not set"


def test_maker_config_missing_signer_key():
    """Test MakerConfig creation fails when SIGNER_PRIV_KEY is missing."""
    # Setup partial environment
    os.environ["MAKER_SESS_ID"] = "test_maker_id"
    os.environ["MAKER_SESS_AUTH"] = "4aa0e0f2-50eb-48a0-b78e-b6bb446ccd7b"
    os.environ.pop("SIGNER_PRIV_KEY", None)

    with pytest.raises(ValueError) as exc_info:
        MakerConfig.from_env()

    assert str(exc_info.value) == "SIGNER_PRIV_KEY env var is not set"


def test_maker_config_invalid_signer_key():
    """Test MakerConfig creation fails when SIGNER_PRIV_KEY is missing."""
    # Setup partial environment
    os.environ["MAKER_SESS_ID"] = "test_maker_id"
    os.environ["MAKER_SESS_AUTH"] = "4aa0e0f2-50eb-48a0-b78e-b6bb446ccd7b"
    os.environ["SIGNER_PRIV_KEY"] = (
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbe"  # Invalid length of pk
    )

    with pytest.raises(ValueError) as exc_info:
        MakerConfig.from_env()

    assert "Invalid SIGNER_PRIV_KEY: The private key must be exactly 32 bytes" in str(
        exc_info.value
    )


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before and after each test."""
    # Save original environment
    orig_env = dict(os.environ)

    # Clean relevant variables
    for key in ["MAKER_SESS_ID", "MAKER_SESS_AUTH", "SIGNER_PRIV_KEY"]:
        os.environ.pop(key, None)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(orig_env)
