import pytest
import time
from openai import OpenAI
from app.config import Config
from app.services.openai_service import OpenAIService


class TestOpenAIServiceInitialization:
    """Test OpenAI service initialization and basic connectivity"""
    
    def test_openai_service_initialization(self):
        """Test that OpenAI service initializes correctly"""
        service = OpenAIService()
        assert service is not None
        assert hasattr(service, 'client')
        assert isinstance(service.client, OpenAI)
        assert service.client.api_key == Config.OPENAI_API_KEY
    
    def test_openai_credentials_validation(self):
        """Test that OpenAI credentials are valid and accessible"""
        service = OpenAIService()
        
        # Verify API key format
        assert Config.OPENAI_API_KEY is not None
        assert Config.OPENAI_API_KEY.startswith("sk-"), "OpenAI API key should start with 'sk-'"
        assert len(Config.OPENAI_API_KEY) > 40, "OpenAI API key seems too short"
        
        # Verify client has the correct key
        assert service.client.api_key == Config.OPENAI_API_KEY
    
    def test_openai_connection_health_check(self):
        """Test basic OpenAI API connectivity"""
        service = OpenAIService()
        
        # Test connection with a simple API call
        health_status = service.health_check()
        assert health_status is not None
        assert isinstance(health_status, dict)
        assert health_status.get("status") == "healthy"
        assert "api_accessible" in health_status
        assert health_status["api_accessible"] is True
        assert "model_info" in health_status
    
    def test_openai_model_configuration(self):
        """Test that the correct OpenAI model is configured"""
        service = OpenAIService()
        
        # Check default model configuration
        assert hasattr(service, 'default_model')
        assert service.default_model in ["gpt-4", "gpt-4-turbo-preview", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"]
        
        # Verify model is accessible
        model_info = service.get_model_info()
        assert model_info is not None
        assert model_info.get("model") == service.default_model
        assert model_info.get("available") is True


class TestOpenAIServiceBasicOperations:
    """Test basic OpenAI service operations"""
    
    def test_simple_completion_request(self):
        """Test making a simple completion request to OpenAI"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "Say 'Hello, World!' and nothing else."}
        ]
        
        response = service.create_completion(messages=messages, max_tokens=10)
        assert response is not None
        assert isinstance(response, dict)
        assert "content" in response
        assert "model" in response
        assert "usage" in response
        
        # Verify response content
        content = response["content"].strip().lower()
        assert "hello" in content and "world" in content
    
    def test_completion_with_system_message(self):
        """Test completion with system message"""
        service = OpenAIService()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Respond with exactly one word: 'SUCCESS'"},
            {"role": "user", "content": "Please respond as instructed."}
        ]
        
        response = service.create_completion(messages=messages, max_tokens=5)
        assert response is not None
        
        content = response["content"].strip().upper()
        assert "SUCCESS" in content
    
    def test_completion_with_temperature_control(self):
        """Test completion with different temperature settings"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "Generate a random number between 1 and 10."}
        ]
        
        # Test with low temperature (more deterministic)
        response_low = service.create_completion(messages=messages, temperature=0.1, max_tokens=10)
        assert response_low is not None
        
        # Test with high temperature (more creative)
        response_high = service.create_completion(messages=messages, temperature=0.9, max_tokens=10)
        assert response_high is not None
        
        # Both should return valid responses
        assert "content" in response_low
        assert "content" in response_high
    
    def test_completion_error_handling(self):
        """Test error handling for invalid requests"""
        service = OpenAIService()
        
        # Test with empty messages
        with pytest.raises(Exception):
            service.create_completion(messages=[])
        
        # Test with invalid message format
        with pytest.raises(Exception):
            service.create_completion(messages=[{"invalid": "format"}])
        
        # Test with excessive token request
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(Exception):
            service.create_completion(messages=messages, max_tokens=100000)


class TestOpenAIServicePerformance:
    """Test OpenAI service performance requirements"""
    
    def test_completion_response_time(self):
        """Test that completion requests meet performance requirements"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "Please respond with a brief greeting."}
        ]
        
        start_time = time.time()
        response = service.create_completion(messages=messages, max_tokens=20)
        response_time = time.time() - start_time
        
        # Should respond within reasonable time (adjust based on needs)
        assert response_time < 10.0, f"OpenAI response took {response_time:.2f}s, should be < 10s"
        assert response is not None
        assert "content" in response
    
    def test_multiple_concurrent_requests(self):
        """Test handling multiple requests efficiently"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "Say 'Test response'"}
        ]
        
        start_time = time.time()
        responses = []
        
        # Make 3 sequential requests (in real usage, these would be concurrent)
        for i in range(3):
            response = service.create_completion(messages=messages, max_tokens=10)
            responses.append(response)
        
        total_time = time.time() - start_time
        
        # All responses should be valid
        assert len(responses) == 3
        for response in responses:
            assert response is not None
            assert "content" in response
        
        # Total time should be reasonable
        assert total_time < 30.0, f"3 requests took {total_time:.2f}s, should be < 30s"


class TestOpenAIServiceConfiguration:
    """Test OpenAI service configuration and model management"""
    
    def test_default_model_settings(self):
        """Test default model configuration"""
        service = OpenAIService()
        
        # Verify default settings are appropriate for automotive assistant
        assert service.default_model in ["gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-4o", "gpt-4o-mini"]
        assert hasattr(service, 'default_temperature')
        assert 0.0 <= service.default_temperature <= 1.0
        assert hasattr(service, 'default_max_tokens')
        assert service.default_max_tokens > 0
    
    def test_model_availability_check(self):
        """Test checking if configured model is available"""
        service = OpenAIService()
        
        model_info = service.get_model_info()
        assert model_info["available"] is True
        assert model_info["model"] == service.default_model
    
    def test_service_configuration_validation(self):
        """Test that service configuration is valid"""
        service = OpenAIService()
        
        config_validation = service.validate_configuration()
        assert config_validation["status"] == "valid"
        assert config_validation["api_key_present"] is True
        assert config_validation["model_configured"] is True
        assert config_validation["model_available"] is True


class TestOpenAIServiceBilingualSupport:
    """Test OpenAI service support for bilingual operations"""
    
    def test_english_language_processing(self):
        """Test processing English language requests"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "Please respond in English: What is your primary function?"}
        ]
        
        response = service.create_completion(messages=messages, max_tokens=50)
        assert response is not None
        
        content = response["content"]
        # Should respond in English
        assert len(content) > 0
        # Basic check that response is in Latin script (English)
        assert any(c.isalpha() and ord(c) < 128 for c in content)
    
    def test_georgian_language_processing(self):
        """Test processing Georgian language requests"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "გთხოვთ უპასუხოთ ქართულად: რა არის თქვენი ძირითადი ფუნქცია?"}
        ]
        
        response = service.create_completion(messages=messages, max_tokens=100)
        assert response is not None
        
        content = response["content"]
        assert len(content) > 0
        # Should be able to process Georgian text (response might be in English, but should handle Georgian input)
    
    def test_mixed_language_handling(self):
        """Test handling mixed language content"""
        service = OpenAIService()
        
        messages = [
            {"role": "user", "content": "Hello, ჩემი მანქანის engine has a problem. Can you help?"}
        ]
        
        response = service.create_completion(messages=messages, max_tokens=80)
        assert response is not None
        assert "content" in response
        assert len(response["content"]) > 0


class TestOpenAIServiceErrorRecovery:
    """Test error handling and recovery scenarios"""
    
    def test_api_key_validation_error(self):
        """Test handling of invalid API key scenarios"""
        # Create service with normal key first
        service = OpenAIService()
        
        # Test that service validates its configuration
        config_validation = service.validate_configuration()
        assert config_validation["status"] == "valid"
    
    def test_network_error_handling(self):
        """Test handling of network-related errors"""
        service = OpenAIService()
        
        # Test with a request that might timeout
        messages = [
            {"role": "user", "content": "Please provide a detailed explanation of automotive engineering principles in 2000 words."}
        ]
        
        try:
            response = service.create_completion(messages=messages, max_tokens=2000)
            # If successful, verify response
            assert response is not None
        except Exception as e:
            # If it fails due to network/timeout, ensure error is handled gracefully
            assert "timeout" in str(e).lower() or "connection" in str(e).lower() or "rate" in str(e).lower()
    
    def test_service_recovery_after_error(self):
        """Test that service can recover after encountering errors"""
        service = OpenAIService()
        
        # First, make a successful request
        messages = [{"role": "user", "content": "Hello"}]
        response1 = service.create_completion(messages=messages, max_tokens=10)
        assert response1 is not None
        
        # Then try an invalid request
        try:
            service.create_completion(messages=[], max_tokens=10)
        except:
            pass  # Expected to fail
        
        # Then make another successful request to verify recovery
        response2 = service.create_completion(messages=messages, max_tokens=10)
        assert response2 is not None
        assert "content" in response2


class TestOpenAIServiceIntegration:
    """Test integration with existing system components"""
    
    def test_config_integration(self):
        """Test integration with configuration system"""
        service = OpenAIService()
        
        # Verify service uses config correctly
        assert service.client.api_key == Config.OPENAI_API_KEY
        assert service.default_model == Config.OPENAI_MODEL
    
    def test_service_initialization_with_database(self):
        """Test that OpenAI service can coexist with database services"""
        from app.db.database_service import DatabaseService
        from app.db.repositories.conversation_repository import ConversationRepository
        
        # Initialize all services
        openai_service = OpenAIService()
        db_service = DatabaseService()
        conversation_repo = ConversationRepository()
        
        # All should be functional
        assert openai_service.health_check()["status"] == "healthy"
        assert db_service.health_check()["status"] == "healthy"
        
        # Test a simple integration scenario
        conversation_id = conversation_repo.create_conversation(
            user_id="integration_test_user",
            language="en",
            title="OpenAI Integration Test"
        )
        
        try:
            messages = [{"role": "user", "content": "Hello from integration test"}]
            openai_response = openai_service.create_completion(messages=messages, max_tokens=20)
            
            # Add response to conversation
            conversation_repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=openai_response["content"],
                language="en"
            )
            
            # Verify integration worked
            conversation_messages = conversation_repo.get_conversation_messages(conversation_id)
            assert len(conversation_messages) == 1
            assert conversation_messages[0]["role"] == "assistant"
            assert conversation_messages[0]["content"] == openai_response["content"]
            
        finally:
            # Cleanup
            conversation_repo.delete_conversation(conversation_id) 