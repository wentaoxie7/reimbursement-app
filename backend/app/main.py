from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth
from app.api.admin import approval_config, fields, page_access, users
from app.api.user import approval, expenses
from app.core.config import settings
from app.db.bootstrap import ensure_database_schema

UPLOAD_ROOT = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

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
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")


@app.on_event("startup")
def startup() -> None:
    ensure_database_schema()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
