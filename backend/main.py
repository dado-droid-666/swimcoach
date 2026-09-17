from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routes import auth, profile, competition, plan, feedback, stats, subscription

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
app.include_router(stats.router)
app.include_router(subscription.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api")
def api_root():
    return {"message": "SwimCoach API", "docs": "/docs"}


# Serve the PWA frontend from the same origin so relative /api calls work.
# Mounted LAST so /api/* and /docs routes take precedence.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")