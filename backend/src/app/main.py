"""
FastAPI Main Application

Entry point for the Vibe Agent backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from .config import get_settings


# Setup logging
def setup_logging():
    """Configure application logging."""
    settings = get_settings()
    
    # Ensure log directory exists
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting Vibe Agent Backend...")
    settings = get_settings()
    settings.ensure_directories()
    logger.info(f"✅ Configuration loaded from: {settings.Config.env_file}")
    logger.info(f"📦 Target repository: {settings.target_repo_path or 'Not set'}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Vibe Agent Backend...")


# Create FastAPI app
app = FastAPI(
    title="Vibe Coding AI Agent",
    description="Autonomous Full-Stack Repository Intelligence System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
settings = get_settings()
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "vibe-agent-backend",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Vibe Coding AI Agent API",
        "version": "1.0.0",
        "description": "Autonomous Repository Intelligence System",
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )


# Import and register routers
from .routes import indexing, debug, chat, search, graph

app.include_router(indexing.router)
app.include_router(debug.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(graph.router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
