"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import auth, comments, feed, likes, posts, users
from app.core.config import settings
from app.core.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(feed.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    """Landing endpoint — confirms the API is up."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "message": "API ishlayapti 🚀",
        "docs": "/docs",
    }


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Health check used by Docker / monitoring."""
    return {"status": "healthy"}
