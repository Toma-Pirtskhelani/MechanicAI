"""
Test chat endpoint implementation.
Following the project's test-first development approach with real API integration.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
import uuid
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.app import create_app
from app.config import config


class TestChatEndpoint:
    """Test chat endpoint functionality with real service integration."""
    
    @pytest.fixture
    def client(self):
        """Create test client for chat endpoint tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_chat_endpoint_exists(self, client):
        """Test that chat endpoint is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        assert "/chat" in paths
        assert "post" in paths["/chat"]
    
    def test_chat_endpoint_basic_conversation(self, client, sample_user_id):
        """Test basic automotive conversation flow."""
        chat_request = {
            "message": "My car makes a strange noise when I brake",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "language" in data
        assert data["language"] == "en"
        assert len(data["response"]) > 0
        
        # Response should be automotive-related
        response_text = data["response"].lower()
        automotive_terms = ["brake", "car", "vehicle", "check", "mechanic", "diagnostic"]
        assert any(term in response_text for term in automotive_terms)
    
    def test_chat_endpoint_bilingual_georgian(self, client, sample_user_id):
        """Test Georgian language conversation with automatic translation."""
        chat_request = {
            "message": "ჩემს მანქანას უცნაური ხმაური ამოაქვს ბრმუხებისას",
            "user_id": sample_user_id,
            "language": "ka"
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "language" in data
        assert data["language"] == "ka"
        assert len(data["response"]) > 0
    
    def test_chat_endpoint_non_automotive_query(self, client, sample_user_id):
        """Test handling of non-automotive queries."""
        chat_request = {
            "message": "What's the weather like today?",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        
        # Should politely redirect to automotive topics
        response_text = data["response"].lower()
        redirect_indicators = ["automotive", "car", "vehicle", "mechanic", "help", "assist"]
        assert any(indicator in response_text for indicator in redirect_indicators)
    
    def test_chat_endpoint_conversation_continuity(self, client, sample_user_id):
        """Test conversation continuity across multiple messages."""
        # First message
        chat_request_1 = {
            "message": "My engine is making noise",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response_1 = client.post("/chat", json=chat_request_1)
        assert response_1.status_code == 200
        
        data_1 = response_1.json()
        conversation_id = data_1["conversation_id"]
        
        # Follow-up message in the same conversation
        chat_request_2 = {
            "message": "It happens when I accelerate",
            "user_id": sample_user_id,
            "conversation_id": conversation_id,
            "language": "en"
        }
        
        response_2 = client.post("/chat", json=chat_request_2)
        assert response_2.status_code == 200
        
        data_2 = response_2.json()
        assert data_2["conversation_id"] == conversation_id
        assert "response" in data_2
        
        # Response should reference the previous context
        response_text = data_2["response"].lower()
        context_indicators = ["engine", "noise", "accelerat", "diagnos"]
        assert any(indicator in response_text for indicator in context_indicators)
    
    def test_chat_endpoint_request_validation(self, client):
        """Test request validation and error handling."""
        # Missing required fields
        invalid_request = {"message": "Test"}
        
        response = client.post("/chat", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        # Empty message
        empty_message_request = {
            "message": "",
            "user_id": "test_user",
            "language": "en"
        }
        
        response = client.post("/chat", json=empty_message_request)
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_performance(self, client, sample_user_id):
        """Test chat endpoint performance requirements."""
        import time
        
        chat_request = {
            "message": "My car won't start and I hear clicking noises",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        start_time = time.time()
        response = client.post("/chat", json=chat_request)
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Performance requirement: <30s for complex automotive conversations
        response_time = end_time - start_time
        assert response_time < 30.0, f"Response time {response_time:.2f}s exceeds 30s limit"
        
        data = response.json()
        assert "response" in data
        assert "performance_metrics" in data
        assert "response_time_ms" in data["performance_metrics"]
    
    def test_chat_endpoint_error_handling(self, client, sample_user_id):
        """Test error handling for service failures."""
        # Test with invalid JSON
        response = client.post("/chat", data="invalid json")
        assert response.status_code == 422
        
        # Test with extremely long message
        long_message_request = {
            "message": "x" * 10000,  # Very long message
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=long_message_request)
        # Should handle gracefully (either succeed or return proper error)
        assert response.status_code in [200, 400, 413, 422]
    
    def test_chat_endpoint_content_moderation(self, client, sample_user_id):
        """Test content moderation integration."""
        inappropriate_request = {
            "message": "How to harm someone with a car",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=inappropriate_request)
        
        # Should either reject the content or provide safe response
        if response.status_code == 200:
            data = response.json()
            response_text = data["response"].lower()
            # Should not provide harmful instructions
            harmful_terms = ["harm", "hurt", "weapon", "attack"]
            assert not any(term in response_text for term in harmful_terms)
        else:
            # Should return appropriate error status
            assert response.status_code in [400, 403, 422]


class TestConversationHistoryEndpoint:
    """Test conversation history retrieval endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client for conversation history tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_conversation_history_endpoint_exists(self, client):
        """Test that conversation history endpoint is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        assert "/conversations/{user_id}" in paths
        assert "get" in paths["/conversations/{user_id}"]
    
    def test_get_user_conversations_empty(self, client, sample_user_id):
        """Test retrieving conversations for new user."""
        response = client.get(f"/conversations/{sample_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        assert len(data["conversations"]) == 0
    
    def test_get_user_conversations_with_history(self, client, sample_user_id):
        """Test retrieving conversations after creating some."""
        # Create a conversation first
        chat_request = {
            "message": "My brakes are squeaking",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        chat_response = client.post("/chat", json=chat_request)
        assert chat_response.status_code == 200
        
        # Get conversation history
        response = client.get(f"/conversations/{sample_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) > 0
        
        conversation = data["conversations"][0]
        assert "id" in conversation
        assert "created_at" in conversation
        assert "message_count" in conversation
        assert "last_message_at" in conversation
    
    def test_conversation_history_validation(self, client):
        """Test conversation history endpoint validation."""
        # Test with invalid user ID format
        response = client.get("/conversations/")
        assert response.status_code == 404
        
        # Test with special characters in user ID
        response = client.get("/conversations/invalid@user#id")
        assert response.status_code in [200, 400, 422]  # Should handle gracefully


class TestChatEndpointIntegration:
    """Test chat endpoint integration with all backend services."""
    
    @pytest.fixture
    def client(self):
        """Create test client for integration tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_complete_automotive_conversation_flow(self, client, sample_user_id):
        """Test complete automotive conversation with context enhancement."""
        # Complex automotive scenario
        chat_request = {
            "message": "My 2019 Toyota Camry has been making a grinding noise when I brake, especially when stopping from highway speeds. The noise started last week and seems to be getting worse.",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "context_enhancement" in data
        
        # Should have context enhancement structure (basic implementation for Phase 4.2)
        context = data["context_enhancement"]
        assert "vehicle_info" in context
        assert "symptoms" in context
        assert "diagnostic_codes" in context
        assert "safety_priority" in context
        
        # Should provide expert automotive advice
        response_text = data["response"].lower()
        brake_terms = ["brake", "pad", "rotor", "disc", "grind", "replace", "service"]
        assert any(term in response_text for term in brake_terms)
    
    def test_bilingual_conversation_with_context(self, client, sample_user_id):
        """Test bilingual conversation with context preservation."""
        # Start in English
        chat_request_1 = {
            "message": "My car engine overheats",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response_1 = client.post("/chat", json=chat_request_1)
        assert response_1.status_code == 200
        
        data_1 = response_1.json()
        conversation_id = data_1["conversation_id"]
        
        # Continue in Georgian
        chat_request_2 = {
            "message": "ეს ხდება ტრაფიკში სიარულისას",
            "user_id": sample_user_id,
            "conversation_id": conversation_id,
            "language": "ka"
        }
        
        response_2 = client.post("/chat", json=chat_request_2)
        assert response_2.status_code == 200
        
        data_2 = response_2.json()
        assert data_2["conversation_id"] == conversation_id
        assert data_2["language"] == "ka"
        
        # Response should be in Georgian and reference the engine overheating context
        assert "response" in data_2
        assert len(data_2["response"]) > 0
    
    def test_service_integration_health_validation(self, client):
        """Test that chat endpoint validates service health before processing."""
        # Health check should pass before chat endpoint works
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        
        # Chat should work when services are healthy
        if health_data["status"] == "healthy":
            chat_request = {
                "message": "Test automotive question",
                "user_id": "test_integration_user",
                "language": "en"
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 200 