from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_projects() -> dict[str, list[dict[str, str | int]]]:
    return {
        "items": [
            {"id": 1, "name": "CRM 重构", "status": "进行中", "manager": "王强"},
            {"id": 2, "name": "数据中台", "status": "进行中", "manager": "李敏"},
        ]
    }
