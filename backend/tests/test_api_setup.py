"""
Test FastAPI application setup and initialization.
Following the project's test-first development approach with real API integration.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.app import create_app
from app.config import config


class TestFastAPISetup:
    """Test FastAPI application initialization and basic functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client for FastAPI application."""
        app = create_app()
        return TestClient(app)
    
    def test_app_creation(self):
        """Test that FastAPI app can be created successfully."""
        app = create_app()
        assert app is not None
        assert hasattr(app, 'title')
        assert hasattr(app, 'version')
    
    def test_app_metadata(self):
        """Test FastAPI app metadata is correctly set."""
        app = create_app()
        assert app.title == "MechaniAI API"
        assert app.description is not None
        assert app.version == "1.0.0"
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint is available and returns correct response."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs_url" in data
    
    def test_docs_endpoint_available(self, client):
        """Test that OpenAPI docs endpoint is available."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is properly generated."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "MechaniAI API"
    
    def test_cors_configuration(self):
        """Test CORS middleware is properly configured."""
        app = create_app()
        # Check that CORS middleware is added to the app
        middleware_classes = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes
    
    def test_app_startup_event(self, client):
        """Test that application startup event executes successfully."""
        # This test verifies that the app can start without errors
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_error_handling_middleware(self, client):
        """Test that error handling middleware is properly configured."""
        # Test accessing a non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data


class TestAPIConfiguration:
    """Test API configuration and environment integration."""
    
    def test_configuration_loading(self):
        """Test that configuration is properly loaded for API."""
        assert config.OPENAI_API_KEY is not None
        assert config.SUPABASE_URL is not None
        assert config.SUPABASE_KEY is not None
    
    def test_debug_mode_setting(self):
        """Test debug mode configuration."""
        app = create_app()
        # Debug mode should be disabled in production
        assert hasattr(app, 'debug')


class TestAPIIntegration:
    """Test API integration with core services."""
    
    @pytest.fixture
    def client(self):
        """Create test client for integration tests."""
        app = create_app()
        return TestClient(app)
    
    def test_service_dependencies_available(self, client):
        """Test that core services are properly initialized and available."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        # Health check should verify service dependencies
        assert data["status"] == "healthy"
    
    def test_api_versioning(self, client):
        """Test API versioning is properly implemented."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0" 