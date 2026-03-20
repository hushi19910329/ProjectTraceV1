from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def login(account: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"account": account, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_update_user_status_and_roles() -> None:
    admin_token = login("admin", "admin123")

    create_resp = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "tester01",
            "real_name": "测试用户",
            "mobile": "13700000001",
            "password": "test123",
            "status": "active",
            "role_ids": [],
        },
    )
    assert create_resp.status_code == 200
    user_id = create_resp.json()["id"]

    roles_resp = client.get("/api/v1/users/meta/roles", headers={"Authorization": f"Bearer {admin_token}"})
    assert roles_resp.status_code == 200
    developer_role = next(item for item in roles_resp.json()["items"] if item["code"] == "developer")

    update_resp = client.put(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "real_name": "测试用户-更新",
            "mobile": "13700000001",
            "status": "disabled",
            "role_ids": [developer_role["id"]],
        },
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["status"] == "disabled"
    assert body["real_name"] == "测试用户-更新"
    assert developer_role["id"] in body["role_ids"]
