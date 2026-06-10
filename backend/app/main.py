from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth
from app.api.admin import approval_config, fields, page_access, users
from app.api.user import approval, expenses
from app.core.config import settings

app = FastAPI(
    title="Reimbursement API",
    description="User + Admin dual portal backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(approval.router, prefix="/api")
app.include_router(fields.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(approval_config.router, prefix="/api")
app.include_router(page_access.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
