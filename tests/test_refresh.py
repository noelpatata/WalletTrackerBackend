import pytest
from utils.Constants import TokenMessages, AuthMessages


def login(client):
    response = client.post("/api/v1/login/", json={
        "username": "testuser",
        "password": "password123"
    })
    return response.get_json()["data"]["token"]


def test_refresh_success(client):
    token = login(client)
    response = client.post(
        "/api/v1/refresh/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["message"] == TokenMessages.REFRESHED
    assert "token" in data["data"]
    assert isinstance(data["data"]["token"], str) and len(data["data"]["token"]) > 0


def test_refresh_returns_different_token(client):
    token = login(client)
    new_token = client.post(
        "/api/v1/refresh/",
        headers={"Authorization": f"Bearer {token}"}
    ).get_json()["data"]["token"]
    assert token != new_token


def test_refresh_rotated_token_is_invalid(client):
    token = login(client)
    client.post("/api/v1/refresh/", headers={"Authorization": f"Bearer {token}"})
    # Using the original token again should fail (jti revoked)
    response = client.post(
        "/api/v1/refresh/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.get_json()["message"] == TokenMessages.REFRESH_INVALID


def test_refresh_revoked_token_revokes_all_sessions(client):
    token_a = login(client)
    token_b = login(client)

    # Refresh token_a to rotate it — its jti is now revoked
    client.post("/api/v1/refresh/", headers={"Authorization": f"Bearer {token_a}"})

    # Use the old token_a again (revoked jti) — should trigger full revocation
    client.post("/api/v1/refresh/", headers={"Authorization": f"Bearer {token_a}"})

    # token_b should also be revoked now
    response = client.post(
        "/api/v1/refresh/",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 401


def test_refresh_missing_header(client):
    response = client.post("/api/v1/refresh/")
    assert response.status_code == 415
    assert response.get_json()["message"] == AuthMessages.INVALID_HEADERS


def test_refresh_invalid_token(client):
    response = client.post(
        "/api/v1/refresh/",
        headers={"Authorization": "Bearer notavalidtoken"}
    )
    assert response.status_code == 401
    assert response.get_json()["message"] == TokenMessages.INVALID


def test_logout_success(client):
    token = login(client)
    response = client.post(
        "/api/v1/logout/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == TokenMessages.LOGGED_OUT


def test_logout_invalidates_refresh(client):
    token = login(client)
    client.post("/api/v1/logout/", headers={"Authorization": f"Bearer {token}"})
    response = client.post(
        "/api/v1/refresh/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_logout_missing_header(client):
    response = client.post("/api/v1/logout/")
    assert response.status_code == 415
    assert response.get_json()["message"] == AuthMessages.INVALID_HEADERS
