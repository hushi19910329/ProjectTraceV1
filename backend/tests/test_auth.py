from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_by_username() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "admin"


def test_login_by_mobile() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"account": "13800000000", "password": "admin123"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["mobile"] == "13800000000"


def test_current_user() -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"account": "admin", "password": "admin123"},
    )
    token = login_response.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "admin"
