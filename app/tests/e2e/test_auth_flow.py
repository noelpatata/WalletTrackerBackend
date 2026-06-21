import pytest
import requests

pytestmark = pytest.mark.e2e


def test_health(base_url):
    response = requests.get(f"{base_url}/api/v1/health", timeout=10)
    assert response.status_code == 200


def test_register_and_login(base_url):
    username = "e2e_testuser"
    register_payload = {
        "username": username,
        "password": "e2e_password123"
    }

    register_response = requests.post(
        f"{base_url}/api/v1/register/",
        json=register_payload,
        timeout=10
    )
    assert register_response.status_code == 200

    login_response = requests.post(
        f"{base_url}/api/v1/login/",
        json=register_payload,
        timeout=10
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert data["success"] is True
    assert "token" in data["data"]


def test_refresh_token(base_url):
    username = "e2e_refreshuser"

    register_payload = {
        "username": username,
        "password": "e2e_password123"
    }
    requests.post(
        f"{base_url}/api/v1/register/",
        json=register_payload,
        timeout=10
    )

    login_response = requests.post(
        f"{base_url}/api/v1/login/",
        json=register_payload,
        timeout=10
    )
    token = login_response.json()["data"]["token"]

    refresh_response = requests.post(
        f"{base_url}/api/v1/refresh/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    assert refresh_response.status_code == 200
    assert "token" in refresh_response.json()["data"]


def test_logout(base_url):
    username = "e2e_logoutuser"

    register_payload = {
        "username": username,
        "password": "e2e_password123"
    }
    requests.post(
        f"{base_url}/api/v1/register/",
        json=register_payload,
        timeout=10
    )

    login_response = requests.post(
        f"{base_url}/api/v1/login/",
        json=register_payload,
        timeout=10
    )
    token = login_response.json()["data"]["token"]

    logout_response = requests.post(
        f"{base_url}/api/v1/logout/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    assert logout_response.status_code == 200
