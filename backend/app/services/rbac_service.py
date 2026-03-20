from app.services.menu_service import build_menu_tree, get_available_modules


def build_permission_map() -> dict[str, str]:
    return {item["key"]: item["label"] for item in get_available_modules()}


def build_effective_permissions(role_codes: list[str], role_permission_codes: dict[str, list[str]]) -> list[str]:
    permission_codes: set[str] = set()
    for role_code in role_codes:
        permission_codes.update(role_permission_codes.get(role_code, []))
    return sorted(permission_codes)


def build_menus_from_permissions(permission_codes: list[str]) -> list[dict]:
    return build_menu_tree(permission_codes)
