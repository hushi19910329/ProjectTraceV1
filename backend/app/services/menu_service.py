MENU_TREE = [
    {
        "key": "dashboard",
        "label": "工作台",
        "path": "/dashboard",
        "children": [
            {"key": "dashboard-home", "label": "工作台首页", "path": "/dashboard"},
        ],
    },
    {
        "key": "project",
        "label": "项目管理",
        "path": "/projects/list",
        "children": [
            {"key": "project-list", "label": "项目清单", "path": "/projects/list"},
            {"key": "project-task-list", "label": "任务清单", "path": "/projects/tasks"},
            {"key": "project-followed-projects", "label": "关注项目", "path": "/projects/followed-projects"},
            {"key": "project-followed-tasks", "label": "关注任务", "path": "/projects/followed-tasks"},
        ],
    },
    {
        "key": "requirement",
        "label": "需求管理",
        "path": "/requirements",
        "children": [
            {"key": "requirement-list", "label": "需求中心", "path": "/requirements"},
            {"key": "requirement-backlog", "label": "需求池", "path": "/requirements/backlog"},
        ],
    },
    {
        "key": "task",
        "label": "任务管理",
        "path": "/tasks",
        "children": [
            {"key": "task-board", "label": "任务看板", "path": "/tasks"},
            {"key": "task-calendar", "label": "任务日历", "path": "/tasks/calendar"},
        ],
    },
    {
        "key": "test",
        "label": "测试缺陷",
        "path": "/quality/tests",
        "children": [
            {"key": "test-center", "label": "测试中心", "path": "/quality/tests"},
            {"key": "bug-center", "label": "缺陷中心", "path": "/quality/bugs"},
        ],
    },
    {
        "key": "collaboration",
        "label": "工时协同",
        "path": "/collaboration/timesheet",
        "children": [
            {"key": "timesheet", "label": "工时管理", "path": "/collaboration/timesheet"},
            {"key": "message", "label": "消息待办", "path": "/collaboration/messages"},
        ],
    },
    {
        "key": "okr-report",
        "label": "OKR与报表",
        "path": "/insight/okr",
        "children": [
            {"key": "okr", "label": "OKR中心", "path": "/insight/okr"},
            {"key": "report", "label": "统计报表", "path": "/insight/reports"},
        ],
    },
    {
        "key": "system",
        "label": "系统管理",
        "path": "/system/users",
        "children": [
            {"key": "user-management", "label": "用户管理", "path": "/system/users"},
            {"key": "permission-management", "label": "权限说明", "path": "/system/permissions"},
        ],
    },
]


def get_available_modules() -> list[dict[str, str]]:
    return [{"key": item["key"], "label": item["label"]} for item in MENU_TREE]


def build_menu_tree(module_permissions: list[str]) -> list[dict]:
    return [item for item in MENU_TREE if item["key"] in module_permissions]
