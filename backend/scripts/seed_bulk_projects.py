import argparse
import random
from datetime import date, timedelta
from pathlib import Path
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.init_db import init_database
from app.db.postgres import engine
from app.models import (
    Notification,
    OperationLog,
    Project,
    ProjectMember,
    ProjectNode,
    Task,
    TaskComment,
    TaskStatusUpdate,
    User,
)


PROJECT_PREFIX = "SIM-PROJ-"

PROJECT_STATUS = ["not_started", "in_progress", "paused", "done"]
PROJECT_PRIORITY = ["low", "medium", "high", "urgent"]
TASK_STATUS = ["todo", "in_progress", "blocked", "done"]
TASK_PRIORITY = ["low", "medium", "high", "urgent"]
TASK_TYPES = ["development", "testing", "design", "ops", "integration"]

PROJECT_TAG_POOL = [
    "web",
    "mobile",
    "api",
    "analytics",
    "security",
    "data",
    "infra",
    "report",
    "okr",
    "ops",
    "ux",
    "performance",
]
TASK_TAG_POOL = [
    "login",
    "permission",
    "database",
    "frontend",
    "backend",
    "bugfix",
    "refactor",
    "deploy",
    "monitor",
    "testing",
    "docs",
    "review",
]

COMMENTS_POOL = [
    "这部分已经完成首轮开发，待联调验证。",
    "已同步最新进度，请相关同学确认。",
    "发现边界问题，准备补充修复方案。",
    "计划今日完成并提交测试环境。",
    "需要补一条监控规则，避免回归。",
    "这个任务拆分后更易推进，建议先做核心部分。",
]

STATUS_UPDATE_POOL = [
    "今日推进顺利，核心逻辑已完成。",
    "联调阶段发现数据格式兼容问题，正在修复。",
    "完成阶段性里程碑，准备进入下一环节。",
    "受依赖接口影响暂时阻塞，已发起协同提醒。",
    "代码已提交，等待测试反馈。",
]


def random_date_range(base_day: date, i: int) -> tuple[str, str]:
    start = base_day + timedelta(days=i % 120)
    end = start + timedelta(days=random.randint(10, 45))
    return start.isoformat(), end.isoformat()


def choose_users(users: list[User], k: int) -> list[User]:
    k = max(1, min(k, len(users)))
    return random.sample(users, k)


def reset_sim_data(db: Session) -> None:
    projects = db.scalars(select(Project).where(Project.code.like(f"{PROJECT_PREFIX}%"))).all()
    for item in projects:
        db.delete(item)
    db.flush()


def build_project_code(index: int) -> str:
    return f"{PROJECT_PREFIX}{index:04d}"


def create_bulk_projects(db: Session, users: list[User], count: int) -> dict:
    base_day = date(2026, 1, 1)
    created_project = 0
    created_task = 0
    created_subtask = 0
    created_comment = 0
    created_update = 0
    created_notification = 0

    for i in range(1, count + 1):
        code = build_project_code(i)
        exists = db.scalar(select(Project).where(Project.code == code))
        if exists:
            continue

        owner = random.choice(users)
        creator = random.choice(users)
        members = choose_users(users, random.randint(5, 12))
        if owner not in members:
            members.append(owner)
        if creator not in members:
            members.append(creator)

        start_date, end_date = random_date_range(base_day, i)
        status = random.choice(PROJECT_STATUS)
        priority = random.choice(PROJECT_PRIORITY)
        tags = random.sample(PROJECT_TAG_POOL, random.randint(2, 4))

        project = Project(
            code=code,
            name=f"模拟项目 {i:04d}",
            description=f"用于压测与演示的模拟项目 {i:04d}，覆盖任务协作、评论和关注流程。",
            status=status,
            priority=priority,
            owner_id=owner.id,
            created_by_id=creator.id,
            start_date=start_date,
            end_date=end_date,
            goal="提升协作效率与透明度，按节奏完成目标交付。",
            tags=",".join(tags),
        )
        watcher_count = random.randint(2, min(6, len(members)))
        project.watchers = random.sample(members, watcher_count)
        db.add(project)
        db.flush()
        created_project += 1

        for m in members:
            role = "member"
            if m.id == owner.id:
                role = "owner"
            elif m.id == creator.id:
                role = "manager"
            db.add(ProjectMember(project_id=project.id, user_id=m.id, role=role))

        node_names = ["需求澄清", "开发实现", "测试验证", "上线准备"]
        nodes = []
        for idx, node_name in enumerate(node_names, 1):
            node_owner = random.choice(members)
            node = ProjectNode(
                project_id=project.id,
                name=node_name,
                description=f"{node_name}阶段工作内容",
                sequence=idx,
                status=random.choice(PROJECT_STATUS),
                owner_id=node_owner.id,
                start_date=start_date,
                end_date=end_date,
                output_summary=f"{node_name}阶段输出持续更新中",
            )
            db.add(node)
            db.flush()
            nodes.append(node)

        top_task_count = random.randint(5, 10)
        for t in range(top_task_count):
            task_creator = random.choice(members)
            assignee = random.choice(members)
            task_status = random.choice(TASK_STATUS)
            progress = random.randint(0, 100)
            if task_status == "done":
                progress = 100
            task = Task(
                project_id=project.id,
                node_id=random.choice(nodes).id,
                parent_task_id=None,
                title=f"任务 {i:04d}-{t + 1:02d}",
                description="模拟任务：用于展示列表、筛选、进度和协作关系。",
                task_type=random.choice(TASK_TYPES),
                status=task_status,
                priority=random.choice(TASK_PRIORITY),
                tags=",".join(random.sample(TASK_TAG_POOL, random.randint(2, 4))),
                progress=progress,
                creator_id=task_creator.id,
                assignee_id=assignee.id,
                start_date=start_date,
                end_date=end_date,
                estimated_hours=random.randint(4, 40),
                actual_hours=random.randint(0, 36),
                acceptance_criteria="满足业务验收标准并通过基础回归测试。",
                is_abandoned=False,
                abandoned_reason="",
            )
            collab_count = random.randint(1, min(4, len(members)))
            watch_count = random.randint(1, min(4, len(members)))
            task.collaborators = random.sample(members, collab_count)
            task.watchers = random.sample(members, watch_count)
            db.add(task)
            db.flush()
            created_task += 1

            # 状态更新
            update_count = random.randint(2, 4)
            for _ in range(update_count):
                operator = random.choice(members)
                db.add(
                    TaskStatusUpdate(
                        task_id=task.id,
                        status=random.choice(TASK_STATUS),
                        progress=random.randint(0, 100),
                        actual_hours=random.randint(0, 40),
                        content=random.choice(STATUS_UPDATE_POOL),
                        operator_id=operator.id,
                    )
                )
                created_update += 1

            # 评论 + @ + 通知
            comment_count = random.randint(1, 4)
            for _ in range(comment_count):
                author = random.choice(members)
                comment = TaskComment(
                    task_id=task.id,
                    content=random.choice(COMMENTS_POOL),
                    author_id=author.id,
                )
                mention_candidates = [x for x in members if x.id != author.id]
                mention_size = random.randint(0, min(2, len(mention_candidates)))
                if mention_size > 0:
                    mentioned = random.sample(mention_candidates, mention_size)
                    comment.mentioned_users = mentioned
                    for u in mentioned:
                        db.add(
                            Notification(
                                user_id=u.id,
                                project_id=project.id,
                                task_id=task.id,
                                notification_type="comment_mention",
                                title="你被评论@提醒",
                                content=f"任务 {task.title} 中提到了你",
                                is_read=False,
                            )
                        )
                        created_notification += 1
                db.add(comment)
                created_comment += 1

            # 子任务
            sub_count = random.randint(1, 3)
            for s in range(sub_count):
                sub_assignee = random.choice(members)
                sub_status = random.choice(TASK_STATUS)
                sub_progress = random.randint(0, 100)
                if sub_status == "done":
                    sub_progress = 100
                subtask = Task(
                    project_id=project.id,
                    node_id=task.node_id,
                    parent_task_id=task.id,
                    title=f"子任务 {i:04d}-{t + 1:02d}-{s + 1}",
                    description="模拟子任务：用于树状层级与状态流转展示。",
                    task_type="subtask",
                    status=sub_status,
                    priority=random.choice(TASK_PRIORITY),
                    tags=",".join(random.sample(TASK_TAG_POOL, random.randint(1, 3))),
                    progress=sub_progress,
                    creator_id=task_creator.id,
                    assignee_id=sub_assignee.id,
                    start_date=start_date,
                    end_date=end_date,
                    estimated_hours=random.randint(2, 20),
                    actual_hours=random.randint(0, 18),
                    acceptance_criteria="子任务验收通过。",
                    is_abandoned=False,
                    abandoned_reason="",
                )
                subtask.watchers = random.sample(members, random.randint(1, min(3, len(members))))
                db.add(subtask)
                db.flush()
                created_subtask += 1

            # 操作日志
            db.add(
                OperationLog(
                    project_id=project.id,
                    task_id=task.id,
                    operator_id=task_creator.id,
                    action="task_seeded",
                    detail=f"批量造数创建任务 {task.title}",
                )
            )

        if i % 20 == 0:
            db.commit()

    db.commit()
    return {
        "project": created_project,
        "task": created_task,
        "subtask": created_subtask,
        "comment": created_comment,
        "status_update": created_update,
        "notification": created_notification,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed many projects/tasks/comments for realistic demo.")
    parser.add_argument("--count", type=int, default=250, help="How many projects to create. default=250")
    parser.add_argument("--reset", action="store_true", help="Delete existing SIM-PROJ-* projects before seeding.")
    parser.add_argument("--seed", type=int, default=20260320, help="Random seed for reproducibility.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    init_database()

    with Session(engine) as db:
        users = db.scalars(select(User).where(User.status == "active").order_by(User.id)).all()
        if len(users) < 8:
            raise RuntimeError("active users are not enough. please create more users first.")
        if args.reset:
            reset_sim_data(db)
            db.commit()
        result = create_bulk_projects(db, users, args.count)
        print("Bulk simulation data ready.")
        print(f"Projects created: {result['project']}")
        print(f"Tasks created: {result['task']}")
        print(f"Subtasks created: {result['subtask']}")
        print(f"Comments created: {result['comment']}")
        print(f"Status updates created: {result['status_update']}")
        print(f"Notifications created: {result['notification']}")
        print(f"Project code prefix: {PROJECT_PREFIX}")


if __name__ == "__main__":
    main()
