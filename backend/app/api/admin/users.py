from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.permission import Role, UserRoleAssignment
from app.models.user import User
from app.schemas.admin import RoleResponse, UserResponse, UserRolesUpdate
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    user: User = Depends(require_permission("CONFIG_USERS")),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    users = db.scalars(select(User).where(User.org_id == user.org_id)).all()
    result = []
    for u in users:
        role_codes: list[str] = []
        for a in u.role_assignments:
            role = db.get(Role, a.role_id)
            if role:
                role_codes.append(role.code)
        result.append(
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                active=u.active,
                role_codes=role_codes,
            )
        )
    return result


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    user: User = Depends(require_permission("CONFIG_USERS")),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    roles = db.scalars(select(Role).order_by(Role.code)).all()
    return [RoleResponse.model_validate(role) for role in roles]


@router.put("/users/{user_id}/roles", response_model=MessageResponse)
def update_user_roles(
    user_id: str,
    body: UserRolesUpdate,
    admin: User = Depends(require_permission("CONFIG_USERS")),
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
