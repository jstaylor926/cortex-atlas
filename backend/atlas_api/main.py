"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import notes, tasks, events, projects, conversations, ai, settings as settings_router, dashboard, search
from .database import init_db
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting Atlas API...")
    init_db()
    print(f"Database initialized at {settings.database_path}")
    yield
    # Shutdown
    print("Shutting down Atlas API...")


app = FastAPI(
    title="Atlas API",
    version="1.0.0",
    description="Local-first personal OS backend",
    lifespan=lifespan
)

# CORS for Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "atlas-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Atlas API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Register routers
app.include_router(notes.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(search.router, prefix="/api")
