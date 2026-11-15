from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import check_db_connection, init_db
from .routes import auth, profile, competition, plan, feedback, stats, subscription, swimtests, notifications

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(competition.router)
app.include_router(plan.router)
app.include_router(feedback.router)
app.include_router(swimtests.router)
app.include_router(stats.router)
app.include_router(subscription.router)
app.include_router(notifications.router)


@app.get("/api/health")
def health():
    """Liveness only (fast, no DB). Render healthCheckPath uses this so a DB
    outage never causes a restart loop. For DB status use /api/health/db."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/health/db")
def health_db():
    """Readiness: verifies the DB connection. 503 when the database is down or
    unreachable (e.g. Supabase paused), instead of a misleading green health."""
    if check_db_connection():
        return {"status": "ok", "app": settings.app_name, "db": "ok"}
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "app": settings.app_name, "db": "down"},
    )


@app.get("/api")
def api_root():
    return {"message": "SwimCoach API", "docs": "/docs"}


# Serve the PWA frontend from the same origin so relative /api calls work.
# Mounted LAST so /api/* and /docs routes take precedence.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")