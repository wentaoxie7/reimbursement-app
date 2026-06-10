from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_any_page_access, require_page_access
from app.db.session import get_db
from app.models.permission import Role, UserRoleAssignment
from app.models.user import User
from app.schemas.admin import RoleResponse, UserResponse, UserRolesUpdate
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    user: User = Depends(
        require_any_page_access(["ADMIN_USERS", "ADMIN_APPROVAL", "ADMIN_PAGE_ACCESS"])
    ),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    users = db.scalars(select(User).where(User.org_id == user.org_id)).all()
    result: list[UserResponse] = []
    for item in users:
        role_codes: list[str] = []
        for assignment in item.role_assignments:
            role = db.get(Role, assignment.role_id)
            if role and role.code != "MANAGER":
                role_codes.append(role.code)
        result.append(
            UserResponse(
                id=item.id,
                email=item.email,
                full_name=item.full_name,
                active=item.active,
                role_codes=role_codes,
            )
        )
    return result


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    user: User = Depends(require_page_access("ADMIN_USERS")),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    roles = db.scalars(select(Role).where(Role.code != "MANAGER").order_by(Role.code)).all()
    return [RoleResponse.model_validate(role) for role in roles]


@router.put("/users/{user_id}/roles", response_model=MessageResponse)
def update_user_roles(
    user_id: str,
    body: UserRolesUpdate,
    admin: User = Depends(require_page_access("ADMIN_USERS")),
    db: Session = Depends(get_db),
) -> MessageResponse:
    target = db.get(User, user_id)
    if not target or target.org_id != admin.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    roles = db.scalars(select(Role).where(Role.id.in_(body.role_ids))).all() if body.role_ids else []
    if len(roles) != len(set(body.role_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id")
    db.query(UserRoleAssignment).filter(UserRoleAssignment.user_id == user_id).delete()
    for role in roles:
        db.add(UserRoleAssignment(user_id=user_id, role_id=role.id))
    db.commit()
    return MessageResponse(message="Roles updated")
