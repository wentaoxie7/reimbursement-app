from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Role, RolePageAccess, UserRoleAssignment

PAGE_DEFINITIONS = [
    {"key": "USER_HOME", "label": "用户端 · 首页", "portal": "user"},
    {"key": "USER_MY_EXPENSES", "label": "用户端 · 我的报销", "portal": "user"},
    {"key": "USER_NEW_EXPENSE", "label": "用户端 · 新建报销", "portal": "user"},
    {"key": "USER_APPROVAL_TASKS", "label": "用户端 · 审核任务", "portal": "user"},
    {"key": "USER_ALL_EXPENSES", "label": "用户端 · 全部报销", "portal": "user"},
    {"key": "USER_SETTINGS", "label": "用户端 · 设置", "portal": "user"},
    {"key": "ADMIN_DASHBOARD", "label": "管理端 · 控制台", "portal": "admin"},
    {"key": "ADMIN_FIELDS", "label": "管理端 · 字段", "portal": "admin"},
    {"key": "ADMIN_USERS", "label": "管理端 · 用户权限", "portal": "admin"},
    {"key": "ADMIN_APPROVAL", "label": "管理端 · 审核顺序", "portal": "admin"},
    {"key": "ADMIN_PAGE_ACCESS", "label": "管理端 · 页面权限", "portal": "admin"},
]

PAGE_KEYS = {page["key"] for page in PAGE_DEFINITIONS}


class PageAccessService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: str) -> list[str]:
        stmt = (
            select(RolePageAccess.page_key)
            .join(Role, Role.id == RolePageAccess.role_id)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == user_id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def has(self, user_id: str, page_key: str) -> bool:
        return page_key in self.list_for_user(user_id)

    def list_pages_with_roles(self) -> list[dict]:
        roles = self.db.scalars(select(Role).where(Role.code != "MANAGER").order_by(Role.code)).all()
        role_by_id = {role.id: role for role in roles}
        assignments = self.db.scalars(select(RolePageAccess)).all()
        role_codes_by_page: dict[str, list[str]] = {page["key"]: [] for page in PAGE_DEFINITIONS}
        role_ids_by_page: dict[str, list[str]] = {page["key"]: [] for page in PAGE_DEFINITIONS}
        for assignment in assignments:
            role = role_by_id.get(assignment.role_id)
            if role and assignment.page_key in PAGE_KEYS:
                role_codes_by_page[assignment.page_key].append(role.code)
                role_ids_by_page[assignment.page_key].append(role.id)
        return [
            {
                **page,
                "role_codes": sorted(role_codes_by_page[page["key"]]),
                "role_ids": sorted(role_ids_by_page[page["key"]]),
            }
            for page in PAGE_DEFINITIONS
        ]

    def replace_assignments(self, page_key: str, role_ids: Iterable[str]) -> None:
        if page_key not in PAGE_KEYS:
            raise ValueError("Unknown page key")
        role_ids = list(dict.fromkeys(role_ids))
        if page_key == "ADMIN_PAGE_ACCESS" and not role_ids:
            raise ValueError("Page access config page must keep at least one role")
        roles = self.db.scalars(select(Role).where(Role.id.in_(role_ids))).all() if role_ids else []
        if len(roles) != len(role_ids):
            raise ValueError("Invalid role id")
        self.db.query(RolePageAccess).filter(RolePageAccess.page_key == page_key).delete()
        for role_id in role_ids:
            self.db.add(RolePageAccess(role_id=role_id, page_key=page_key))
        self.db.commit()
