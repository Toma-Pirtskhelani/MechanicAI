"""
Main entry point for MechaniAI FastAPI application.
This module serves as the application entry point for ASGI servers like uvicorn.
"""

from app.api.app import app

# Entry point for ASGI servers
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 