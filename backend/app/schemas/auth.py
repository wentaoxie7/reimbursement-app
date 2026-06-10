from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    permissions: list[str]


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)
