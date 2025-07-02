"""
FastAPI application setup and configuration for MechaniAI.
Following the project's architecture and development standards.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.config import config
from app.core.chat_service import ChatService
from app.db.database_service import DatabaseService
from app.services.openai_service import OpenAIService
from app.api.routes.chat import router as chat_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("MechaniAI API starting up...")
    logger.info(f"Configuration loaded: OpenAI model = {config.OPENAI_MODEL}")
    
    # Verify core services can be initialized
    try:
        db_service = DatabaseService()
        openai_service = OpenAIService()
        logger.info("Core services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize core services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("MechaniAI API shutting down...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title="MechaniAI API",
        description="AI-powered automotive assistant for Tegeta Motors providing expert mechanic advice in Georgian and English",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(chat_router, tags=["chat"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler for unhandled errors."""
        logger.error(f"Unhandled error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint returning API information."""
        return {
            "message": "MechaniAI API - AI-powered automotive assistant",
            "version": "1.0.0",
            "docs_url": "/docs",
            "description": "Expert automotive advice in Georgian and English"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint to verify API and service status.
        
        Returns:
            dict: Health status with timestamp and service information
        """
        try:
            # Initialize services for health check
            db_service = DatabaseService()
            openai_service = OpenAIService()
            
            # Perform health checks
            db_healthy = db_service.health_check()
            openai_healthy = openai_service.health_check()
            
            # Determine overall health
            status = "healthy" if db_healthy and openai_healthy else "degraded"
            
            return {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "services": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "openai": "healthy" if openai_healthy else "unhealthy"
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0.0",
                    "error": "Service health check failed"
                }
            )
    
    return app


# Create app instance
app = create_app() 