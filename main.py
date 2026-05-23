from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import create_tables
from app.middleware.logging import LoggingMiddleware
from app.routers import auth, commands

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MNC-Level AI Voice Assistant — Powered by Claude NLP",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(commands.router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION, "service": settings.APP_NAME}

# Static frontend assets (mount after API routes so /api is handled first)
app.mount("/", StaticFiles(directory=".", html=True), name="static")
