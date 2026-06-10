from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission, Role, RolePermission, UserRoleAssignment


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: str) -> list[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.user_id == user_id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def has(self, user_id: str, code: str) -> bool:
        return code in self.list_for_user(user_id)
