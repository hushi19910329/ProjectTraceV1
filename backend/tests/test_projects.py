from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def login(account: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"account": account, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_can_create_project() -> None:
    token = login("admin", "admin123")
    unique_code = f"PRJ-{uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "code": unique_code,
            "name": f"测试项目-{unique_code}",
            "description": "用于验证项目创建流程",
            "status": "not_started",
            "priority": "high",
            "owner_id": 1,
            "start_date": "2026-03-20",
            "end_date": "2026-04-20",
            "goal": "完成项目管理第一版",
            "member_ids": [2],
            "nodes": [{"name": "项目启动", "description": "启动阶段", "sequence": 1}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == unique_code
    assert body["members"]


def test_project_member_can_create_and_abandon_task() -> None:
    admin_token = login("admin", "admin123")
    unique_code = f"TASK-{uuid4().hex[:8]}"
    project_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": unique_code,
            "name": f"任务项目-{unique_code}",
            "description": "用于验证任务流程",
            "status": "in_progress",
            "priority": "medium",
            "owner_id": 2,
            "member_ids": [2],
            "nodes": [{"name": "开发阶段", "description": "执行开发", "sequence": 1}],
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    pm_token = login("pm01", "pm123456")
    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {pm_token}"},
        json={
            "title": "实现项目管理接口",
            "description": "完成项目和任务基础能力",
            "task_type": "development",
            "priority": "high",
            "progress": 10,
        },
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    abandon_response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/abandon",
        headers={"Authorization": f"Bearer {pm_token}"},
        json={"reason": "方案调整，任务改为新任务承接"},
    )
    assert abandon_response.status_code == 200
    assert abandon_response.json()["is_abandoned"] is True
    assert abandon_response.json()["status"] == "abandoned"


def test_notification_can_be_marked_read() -> None:
    admin_token = login("admin", "admin123")
    unique_code = f"MSG-{uuid4().hex[:8]}"
    project_response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": unique_code,
            "name": f"通知项目-{unique_code}",
            "description": "用于验证通知已读",
            "status": "in_progress",
            "priority": "medium",
            "owner_id": 2,
            "member_ids": [2],
            "nodes": [{"name": "执行阶段", "description": "执行中", "sequence": 1}],
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    pm_token = login("pm01", "pm123456")
    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers={"Authorization": f"Bearer {pm_token}"},
        json={"title": "需要管理员关注", "description": "发送提醒", "priority": "high"},
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    reminder_response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/reminders",
        headers={"Authorization": f"Bearer {pm_token}"},
        json={"user_ids": [1], "content": "请确认项目资源安排"},
    )
    assert reminder_response.status_code == 200

    notifications_response = client.get(
        "/api/v1/projects/notifications/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert notifications_response.status_code == 200
    notification_id = notifications_response.json()["items"][0]["id"]

    read_response = client.post(
        f"/api/v1/projects/notifications/{notification_id}/read",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert read_response.status_code == 200
    assert read_response.json()["is_read"] is True
