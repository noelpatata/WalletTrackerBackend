from utils.Constants import UserMessages
def test_login_success(client):
    response = client.post("/api/v1/login/", json={
        "username": "testuser",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["message"] == "Logged in successfully"
    assert "token" in data["data"]
    assert isinstance(data["data"]["token"], str) and len(data["data"]["token"]) > 0

def test_login_user_not_found(client):
    response = client.post("/api/v1/login/", json={
        "username": "testusear",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data["message"] == UserMessages.USER_NOT_FOUND

def test_login_invalid_credentials(client):
    response = client.post("/api/v1/login/", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert data["message"] == UserMessages.USER_NOT_FOUND
