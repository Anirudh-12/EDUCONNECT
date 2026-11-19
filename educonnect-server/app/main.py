import shutil
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.db.seed import seed_data
from app.modules.identity.router import auth_router, device_router
from app.modules.learning.router import learning_router
from app.modules.content.router import content_router
from app.modules.sync.router import sync_router
from app.modules.assessment.router import assessment_router
from app.modules.classroom.router import classroom_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema & default seeds
    init_db()
    seed_data()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "VALIDATION_FAILED",
        401: "UNAUTHENTICATED",
        403: "PERMISSION_DENIED",
        404: "RESOURCE_NOT_FOUND",
        409: "CONFLICT",
        416: "RANGE_NOT_SATISFIABLE",
        429: "RATE_LIMITED",
        500: "SERVER_ERROR",
    }
    raw_message = str(exc.detail)
    error_code = code_map.get(exc.status_code, "SERVER_ERROR")

    # If detail starts with a standard code (e.g. "DEVICE_REVOKED: ...")
    if ":" in raw_message:
        prefix, rest = raw_message.split(":", 1)
        prefix_clean = prefix.strip()
        if prefix_clean.isupper() and "_" in prefix_clean or prefix_clean in code_map.values():
            error_code = prefix_clean
            raw_message = rest.strip()

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": raw_message,
                "details": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "detail": raw_message
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Payload schema validation failed.",
                "details": exc.errors(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "detail": exc.errors()
        }
    )


# Register Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(device_router, prefix=settings.API_V1_PREFIX)
app.include_router(learning_router, prefix=settings.API_V1_PREFIX)
app.include_router(content_router, prefix=settings.API_V1_PREFIX)
app.include_router(sync_router, prefix=settings.API_V1_PREFIX)
app.include_router(assessment_router, prefix=settings.API_V1_PREFIX)
app.include_router(classroom_router, prefix=settings.API_V1_PREFIX)


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    try:
        free_bytes = shutil.disk_usage(".").free
    except Exception:
        free_bytes = 0

    return {
        "status": "healthy",
        "school_server": {
            "name": "Local School Alpha",
            "version": "1.0.0",
            "database": "sqlite_connected",
            "storage_free_bytes": free_bytes,
            "active_clients_est": 1,
            "mode": "offline-local"
        }
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs"
    }
