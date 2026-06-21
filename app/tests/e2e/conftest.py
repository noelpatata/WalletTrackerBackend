import os
import pytest


@pytest.fixture
def base_url():
    return os.environ.get("E2E_BASE_URL", "http://127.0.0.1:5000")
