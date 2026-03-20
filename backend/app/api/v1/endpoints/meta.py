from fastapi import APIRouter
from app.services.menu_service import MENU_TREE, get_available_modules

router = APIRouter()


@router.get("/modules")
def list_modules() -> dict[str, list[dict[str, str]]]:
    return {"items": get_available_modules(), "menus": MENU_TREE}
