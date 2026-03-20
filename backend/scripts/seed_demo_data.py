import argparse
from pathlib import Path
import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.init_db import init_database
from app.db.postgres import engine
from app.models.project_management import (
    Notification,
    OperationLog,
    Project,
    ProjectMember,
    ProjectNode,
    Task,
    TaskComment,
    TaskStatusUpdate,
)
from app.models.rbac import Role, User
from app.services.auth_service import auth_service


DEMO_PROJECT_CODES = {"DEMO-WEB", "DEMO-APP"}
DEMO_USERNAMES = {"demo_pm", "demo_dev1", "demo_dev2", "demo_qa", "demo_ops"}


def get_role(db: Session, code: str) -> Role | None:
    return db.scalar(select(Role).where(Role.code == code))


def get_or_create_user(
    db: Session,
    *,
    username: str,
    real_name: str,
    mobile: str,
    password: str,
    role_code: str,
    is_superuser: bool = False,
) -> User:
    existing = db.scalar(select(User).where(User.username == username))
    if existing:
        return existing

    role = get_role(db, role_code)
    user = User(
        username=username,
        real_name=real_name,
        mobile=mobile,
        password_hash=auth_service.hash_password(password),
        status="active",
        is_superuser=is_superuser,
        roles=[role] if role else [],
    )
    db.add(user)
    db.flush()
    return user


def reset_demo_data(db: Session) -> None:
    demo_projects = db.scalars(select(Project).where(Project.code.in_(DEMO_PROJECT_CODES))).all()
    for project in demo_projects:
        db.delete(project)
    db.flush()

    demo_users = db.scalars(select(User).where(User.username.in_(DEMO_USERNAMES))).all()
    for user in demo_users:
        db.delete(user)
    db.flush()


def create_project_web(db: Session, admin: User, pm: User, dev1: User, dev2: User, qa: User) -> Project:
    existing = db.scalar(select(Project).where(Project.code == "DEMO-WEB"))
    if existing:
        return existing

    project = Project(
        code="DEMO-WEB",
        name="Demo Website Revamp",
        description="Website reconstruction project for internal collaboration and transparency.",
        status="in_progress",
        priority="high",
        owner_id=pm.id,
        created_by_id=admin.id,
        start_date="2026-03-20",
        end_date="2026-04-30",
        goal="Launch a modern website with clear task tracking and reporting.",
        tags="website,internal,frontend",
    )
    project.watchers = [dev1, qa]
    db.add(project)
    db.flush()

    members = [
        ProjectMember(project_id=project.id, user_id=pm.id, role="manager"),
        ProjectMember(project_id=project.id, user_id=dev1.id, role="developer"),
        ProjectMember(project_id=project.id, user_id=dev2.id, role="developer"),
        ProjectMember(project_id=project.id, user_id=qa.id, role="tester"),
    ]
    db.add_all(members)
    db.flush()

    node_design = ProjectNode(
        project_id=project.id,
        name="Design",
        description="UI/UX drafts and interaction review",
        sequence=1,
        status="done",
        owner_id=dev1.id,
        start_date="2026-03-20",
        end_date="2026-03-24",
        output_summary="Prototype approved",
    )
    node_dev = ProjectNode(
        project_id=project.id,
        name="Development",
        description="Core module development",
        sequence=2,
        status="in_progress",
        owner_id=dev2.id,
        start_date="2026-03-25",
        end_date="2026-04-18",
        output_summary="User and project modules are in progress",
    )
    node_test = ProjectNode(
        project_id=project.id,
        name="Testing",
        description="Functional regression and release prep",
        sequence=3,
        status="not_started",
        owner_id=qa.id,
        start_date="2026-04-19",
        end_date="2026-04-30",
        output_summary="Pending",
    )
    db.add_all([node_design, node_dev, node_test])
    db.flush()

    task_auth = Task(
        project_id=project.id,
        node_id=node_dev.id,
        title="Implement login and permission module",
        description="Support login by username or mobile plus role-based menu control.",
        task_type="development",
        status="in_progress",
        priority="high",
        tags="auth,rbac,backend",
        progress=60,
        creator_id=pm.id,
        assignee_id=dev1.id,
        start_date="2026-03-25",
        end_date="2026-04-02",
        estimated_hours=24,
        actual_hours=14,
        acceptance_criteria="Login API and permission checks pass integration tests.",
    )
    task_auth.collaborators = [dev2]
    task_auth.watchers = [pm, qa]
    db.add(task_auth)
    db.flush()

    subtask_login_ui = Task(
        project_id=project.id,
        node_id=node_dev.id,
        parent_task_id=task_auth.id,
        title="Create login UI form",
        description="Build frontend login page and validation states.",
        task_type="subtask",
        status="in_progress",
        priority="medium",
        tags="frontend,login-ui",
        progress=70,
        creator_id=dev1.id,
        assignee_id=dev2.id,
        start_date="2026-03-26",
        end_date="2026-03-30",
        estimated_hours=12,
        actual_hours=9,
        acceptance_criteria="UI can switch username/mobile login modes.",
    )
    subtask_login_ui.watchers = [pm]
    db.add(subtask_login_ui)
    db.flush()

    task_project_page = Task(
        project_id=project.id,
        node_id=node_dev.id,
        title="Build project list and filters",
        description="Support keyword, owner, status, and tag based filtering.",
        task_type="development",
        status="todo",
        priority="medium",
        tags="project,filter,frontend",
        progress=0,
        creator_id=pm.id,
        assignee_id=dev2.id,
        start_date="2026-03-31",
        end_date="2026-04-08",
        estimated_hours=20,
        actual_hours=0,
        acceptance_criteria="Project list can filter by owner and tags.",
    )
    task_project_page.watchers = [pm, qa]
    db.add(task_project_page)
    db.flush()

    c1 = TaskComment(
        task_id=task_auth.id,
        content="@demo_qa Please prepare a test checklist for login edge cases.",
        author_id=pm.id,
    )
    c1.mentioned_users = [qa]
    c2 = TaskComment(
        task_id=task_auth.id,
        content="Backend API is ready. Frontend integration can start now.",
        author_id=dev1.id,
    )
    c3 = TaskComment(
        task_id=subtask_login_ui.id,
        content="@demo_pm mobile login tab style has been aligned with design draft.",
        author_id=dev2.id,
    )
    c3.mentioned_users = [pm]
    db.add_all([c1, c2, c3])

    status_updates = [
        TaskStatusUpdate(
            task_id=task_auth.id,
            status="todo",
            progress=0,
            actual_hours=0,
            content="任务创建，等待开发开始",
            operator_id=pm.id,
        ),
        TaskStatusUpdate(
            task_id=task_auth.id,
            status="in_progress",
            progress=60,
            actual_hours=14,
            content="后端登录接口已完成，进入联调阶段",
            operator_id=dev1.id,
        ),
        TaskStatusUpdate(
            task_id=subtask_login_ui.id,
            status="in_progress",
            progress=70,
            actual_hours=9,
            content="登录页面已实现双模式切换，待细节优化",
            operator_id=dev2.id,
        ),
    ]
    db.add_all(status_updates)

    n1 = Notification(
        user_id=qa.id,
        project_id=project.id,
        task_id=task_auth.id,
        notification_type="mention",
        title="You were mentioned in a comment",
        content="Please prepare a login test checklist.",
        is_read=False,
    )
    n2 = Notification(
        user_id=pm.id,
        project_id=project.id,
        task_id=subtask_login_ui.id,
        notification_type="mention",
        title="You were mentioned in a comment",
        content="Mobile login tab style has been updated.",
        is_read=False,
    )
    db.add_all([n1, n2])

    logs = [
        OperationLog(
            project_id=project.id,
            task_id=task_auth.id,
            operator_id=pm.id,
            action="create_task",
            detail="Created task: Implement login and permission module",
        ),
        OperationLog(
            project_id=project.id,
            task_id=subtask_login_ui.id,
            operator_id=dev1.id,
            action="create_subtask",
            detail="Created subtask: Create login UI form",
        ),
        OperationLog(
            project_id=project.id,
            task_id=task_auth.id,
            operator_id=dev1.id,
            action="update_progress",
            detail="Progress updated to 60%",
        ),
    ]
    db.add_all(logs)
    db.flush()
    return project


def create_project_app(db: Session, admin: User, pm: User, dev1: User, qa: User, ops: User) -> Project:
    existing = db.scalar(select(Project).where(Project.code == "DEMO-APP"))
    if existing:
        return existing

    project = Project(
        code="DEMO-APP",
        name="Demo Mobile App Tracking",
        description="Mobile app project demo with task hierarchy and comment collaboration.",
        status="in_progress",
        priority="medium",
        owner_id=pm.id,
        created_by_id=admin.id,
        start_date="2026-03-22",
        end_date="2026-05-15",
        goal="Deliver V1 app MVP with stable task tracking process.",
        tags="mobile,mvp,tracking",
    )
    project.watchers = [ops]
    db.add(project)
    db.flush()

    members = [
        ProjectMember(project_id=project.id, user_id=pm.id, role="manager"),
        ProjectMember(project_id=project.id, user_id=dev1.id, role="developer"),
        ProjectMember(project_id=project.id, user_id=qa.id, role="tester"),
        ProjectMember(project_id=project.id, user_id=ops.id, role="ops"),
    ]
    db.add_all(members)
    db.flush()

    node_plan = ProjectNode(
        project_id=project.id,
        name="Planning",
        description="MVP scope and milestone setup",
        sequence=1,
        status="done",
        owner_id=pm.id,
        start_date="2026-03-22",
        end_date="2026-03-26",
        output_summary="MVP scope confirmed",
    )
    node_impl = ProjectNode(
        project_id=project.id,
        name="Implementation",
        description="Core feature build",
        sequence=2,
        status="in_progress",
        owner_id=dev1.id,
        start_date="2026-03-27",
        end_date="2026-05-05",
        output_summary="Task module implementation ongoing",
    )
    db.add_all([node_plan, node_impl])
    db.flush()

    task_sync = Task(
        project_id=project.id,
        node_id=node_impl.id,
        title="Implement task sync service",
        description="Synchronize task status across mobile client and backend.",
        task_type="development",
        status="in_progress",
        priority="high",
        tags="sync,backend,mobile",
        progress=45,
        creator_id=pm.id,
        assignee_id=dev1.id,
        start_date="2026-03-28",
        end_date="2026-04-20",
        estimated_hours=36,
        actual_hours=16,
        acceptance_criteria="Task status updates are consistent in all clients.",
    )
    task_sync.watchers = [pm, qa]
    task_sync.collaborators = [ops]
    db.add(task_sync)
    db.flush()

    subtask_alarm = Task(
        project_id=project.id,
        node_id=node_impl.id,
        parent_task_id=task_sync.id,
        title="Add overdue reminder job",
        description="Trigger reminder for overdue tasks every 30 minutes.",
        task_type="subtask",
        status="todo",
        priority="medium",
        tags="reminder,job,notification",
        progress=0,
        creator_id=dev1.id,
        assignee_id=ops.id,
        start_date="2026-04-01",
        end_date="2026-04-10",
        estimated_hours=10,
        actual_hours=0,
        acceptance_criteria="Overdue tasks generate notifications for assignees.",
    )
    db.add(subtask_alarm)

    comment = TaskComment(
        task_id=task_sync.id,
        content="@demo_ops Please help verify scheduler deployment config.",
        author_id=dev1.id,
    )
    comment.mentioned_users = [ops]
    db.add(comment)

    db.add(
        TaskStatusUpdate(
            task_id=task_sync.id,
            status="in_progress",
            progress=45,
            actual_hours=16,
            content="同步服务核心流程已跑通，正在补充失败重试逻辑",
            operator_id=dev1.id,
        )
    )

    notification = Notification(
        user_id=ops.id,
        project_id=project.id,
        task_id=task_sync.id,
        notification_type="mention",
        title="You were mentioned in a comment",
        content="Please verify scheduler deployment config.",
        is_read=False,
    )
    db.add(notification)

    log = OperationLog(
        project_id=project.id,
        task_id=task_sync.id,
        operator_id=dev1.id,
        action="comment_task",
        detail="Mentioned ops to verify deployment scheduler config",
    )
    db.add(log)
    db.flush()
    return project


def create_demo_data(reset: bool) -> None:
    init_database()
    with Session(engine) as db:
        if reset:
            reset_demo_data(db)

        admin = db.scalar(select(User).where(User.username == "admin"))
        if not admin:
            raise RuntimeError("Admin user not found. Please ensure init_database() completed successfully.")

        pm = get_or_create_user(
            db,
            username="demo_pm",
            real_name="Demo PM",
            mobile="13910000001",
            password="demo123456",
            role_code="project-manager",
        )
        dev1 = get_or_create_user(
            db,
            username="demo_dev1",
            real_name="Demo Dev One",
            mobile="13910000002",
            password="demo123456",
            role_code="developer",
        )
        dev2 = get_or_create_user(
            db,
            username="demo_dev2",
            real_name="Demo Dev Two",
            mobile="13910000003",
            password="demo123456",
            role_code="developer",
        )
        qa = get_or_create_user(
            db,
            username="demo_qa",
            real_name="Demo QA",
            mobile="13910000004",
            password="demo123456",
            role_code="developer",
        )
        ops = get_or_create_user(
            db,
            username="demo_ops",
            real_name="Demo Ops",
            mobile="13910000005",
            password="demo123456",
            role_code="developer",
        )
        db.flush()

        p1 = create_project_web(db, admin, pm, dev1, dev2, qa)
        p2 = create_project_app(db, admin, pm, dev1, qa, ops)
        db.commit()

        project_count = db.scalar(
            select(func.count(Project.id)).where(Project.code.in_(DEMO_PROJECT_CODES))
        ) or 0
        task_count = db.scalar(select(func.count(Task.id)).where(Task.project_id.in_([p1.id, p2.id]))) or 0
        comment_count = db.scalar(
            select(func.count(TaskComment.id)).where(
                TaskComment.task_id.in_(select(Task.id).where(Task.project_id.in_([p1.id, p2.id])))
            )
        ) or 0
        note_count = db.scalar(
            select(func.count(Notification.id)).where(Notification.project_id.in_([p1.id, p2.id]))
        ) or 0

        print("Demo data ready.")
        print(f"Projects: {project_count}")
        print(f"Tasks: {task_count}")
        print(f"Comments: {comment_count}")
        print(f"Notifications: {note_count}")
        print("Demo users: demo_pm, demo_dev1, demo_dev2, demo_qa, demo_ops (password: demo123456)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo projects/tasks/comments data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove previous demo data (DEMO-* projects and demo_* users) before seeding.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_demo_data(reset=args.reset)
