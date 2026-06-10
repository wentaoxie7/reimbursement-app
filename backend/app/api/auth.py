from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    TokenResponse,
    UserMeResponse,
)
from app.services.permission import PermissionService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalars(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    perms = PermissionService(db).list_for_user(user.id)
    token = create_access_token(user.id, extra={"permissions": perms})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserMeResponse:
    return UserMeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        permissions=PermissionService(db).list_for_user(user.id),
    )


@router.put("/me", response_model=UserMeResponse)
def update_me(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserMeResponse:
    full_name = body.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required")
    user.full_name = full_name
    db.commit()
    db.refresh(user)
    return UserMeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        permissions=PermissionService(db).list_for_user(user.id),
    )


@router.put("/password")
def change_password(
    body: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"message": "Password updated"}
