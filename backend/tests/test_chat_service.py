import pytest
import asyncio
from typing import Dict, Any, List
from app.core.chat_service import ChatService
from app.config import Config


class TestChatServiceInitialization:
    """Test chat service initialization and dependencies"""
    
    def test_chat_service_initialization(self):
        """Test chat service initializes with all required dependencies"""
        chat_service = ChatService()
        
        # Should have all required service dependencies
        assert hasattr(chat_service, 'openai_service')
        assert hasattr(chat_service, 'conversation_repo')
        assert hasattr(chat_service, 'db_service')
        
        # Services should be properly initialized
        assert chat_service.openai_service is not None
        assert chat_service.conversation_repo is not None
        assert chat_service.db_service is not None
    
    def test_chat_service_health_check(self):
        """Test chat service can verify all dependencies are healthy"""
        chat_service = ChatService()
        
        # Health check should verify all services
        health_status = chat_service.health_check()
        
        assert isinstance(health_status, dict)
        assert 'openai_service' in health_status
        assert 'database_service' in health_status
        assert 'overall_status' in health_status
        
        # All services should be healthy
        assert health_status['openai_service'] is True
        assert health_status['database_service'] is True
        assert health_status['overall_status'] is True


class TestChatFlowIntegration:
    """Test complete chat conversation flow"""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service instance for testing"""
        return ChatService()
    
    @pytest.fixture
    def test_user_id(self):
        """Test user ID for conversation testing"""
        return "test_chat_flow_user"
    
    def test_start_new_conversation(self, chat_service, test_user_id):
        """Test starting a new conversation with language detection"""
        # Test English conversation start
        response = chat_service.start_conversation(
            user_id=test_user_id,
            initial_message="My car engine is making strange noises",
            language="en"
        )
        
        assert isinstance(response, dict)
        assert 'conversation_id' in response
        assert 'response' in response
        assert 'language' in response
        assert response['language'] == 'en'
        assert response['conversation_id'] is not None
        
        # Test Georgian conversation start
        response_ka = chat_service.start_conversation(
            user_id=test_user_id + "_ka",
            initial_message="ჩემი მანქანის ძრავა უცნაური ხმებს გამოსცემს",
            language="ka"
        )
        
        assert response_ka['language'] == 'ka'
        assert response_ka['conversation_id'] is not None
    
    def test_continue_conversation(self, chat_service, test_user_id):
        """Test continuing an existing conversation with context"""
        # Start conversation
        initial_response = chat_service.start_conversation(
            user_id=test_user_id,
            initial_message="My 2015 Toyota Camry engine light is on",
            language="en"
        )
        
        conversation_id = initial_response['conversation_id']
        
        # Continue conversation with follow-up
        follow_up_response = chat_service.process_message(
            user_id=test_user_id,
            conversation_id=conversation_id,
            message="What should I check first?",
            language="en"
        )
        
        assert isinstance(follow_up_response, dict)
        assert 'response' in follow_up_response
        assert 'conversation_id' in follow_up_response
        assert follow_up_response['conversation_id'] == conversation_id
        
        # Response should reference previous context
        response_text = follow_up_response['response'].lower()
        assert 'engine' in response_text or 'light' in response_text or 'camry' in response_text
    
    def test_automotive_relevance_handling(self, chat_service, test_user_id):
        """Test handling of non-automotive queries"""
        # Non-automotive query should be redirected
        response = chat_service.start_conversation(
            user_id=test_user_id,
            initial_message="What's the weather today?",
            language="en"
        )
        
        assert isinstance(response, dict)
        assert 'response' in response
        
        # Should contain polite redirect
        response_text = response['response'].lower()
        assert any(word in response_text for word in ['automotive', 'vehicle', 'car', 'mechanic', 'tegeta'])
    
    def test_bilingual_conversation_flow(self, chat_service, test_user_id):
        """Test complete bilingual conversation handling"""
        # Start in Georgian
        georgian_response = chat_service.start_conversation(
            user_id=test_user_id,
            initial_message="ჩემი BMW-ის ბრეკები ცუდად მუშაობს",
            language="ka"
        )
        
        assert georgian_response['language'] == 'ka'
        conversation_id = georgian_response['conversation_id']
        
        # Continue in English (should auto-translate)
        english_response = chat_service.process_message(
            user_id=test_user_id,
            conversation_id=conversation_id,
            message="How much will brake repair cost?",
            language="en"
        )
        
        assert 'response' in english_response
        # Should maintain conversation context about BMW brakes
        response_text = english_response['response'].lower()
        assert 'brake' in response_text or 'repair' in response_text
    
    def test_content_safety_integration(self, chat_service, test_user_id):
        """Test content moderation integration in chat flow"""
        # Test inappropriate content handling
        try:
            response = chat_service.start_conversation(
                user_id=test_user_id,
                initial_message="This is inappropriate violent content about cars",
                language="en"
            )
            
            # Should either reject or sanitize the response
            assert isinstance(response, dict)
            # If processed, should be safe
            if 'response' in response:
                assert response['response'] is not None
        
        except ValueError as e:
            # Should raise appropriate error for unsafe content
            assert "safety" in str(e).lower() or "moderation" in str(e).lower()


class TestChatServicePerformance:
    """Test chat service performance requirements"""
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_response_time_requirements(self, chat_service):
        """Test chat service meets response time requirements (<10s)"""
        import time
        
        start_time = time.time()
        
        response = chat_service.start_conversation(
            user_id="performance_test_user",
            initial_message="My car won't start, what could be wrong?",
            language="en"
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should complete within 10 seconds
        assert response_time < 10.0
        assert isinstance(response, dict)
        assert 'response' in response
    
    def test_context_compression_performance(self, chat_service):
        """Test context compression triggers appropriately"""
        # Start conversation
        response = chat_service.start_conversation(
            user_id="compression_test_user",
            initial_message="I have a 2018 Honda Civic with transmission issues",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Add multiple messages to trigger context compression
        for i in range(8):  # Should trigger compression around 10 messages
            chat_service.process_message(
                user_id="compression_test_user",
                conversation_id=conversation_id,
                message=f"Follow-up question {i+1} about transmission",
                language="en"
            )
        
        # Verify context compression was applied
        conversation_context = chat_service.conversation_repo.get_active_context(conversation_id)
        
        # Should have an active compressed context
        assert conversation_context is not None
        assert conversation_context['is_active'] is True


class TestChatServiceErrorHandling:
    """Test chat service error handling and recovery"""
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_invalid_conversation_handling(self, chat_service):
        """Test handling of invalid conversation IDs"""
        with pytest.raises(ValueError) as exc_info:
            chat_service.process_message(
                user_id="test_user",
                conversation_id="non_existent_conversation",
                message="Test message",
                language="en"
            )
        
        assert "conversation" in str(exc_info.value).lower()
    
    def test_empty_message_handling(self, chat_service):
        """Test handling of empty or invalid messages"""
        with pytest.raises(ValueError) as exc_info:
            chat_service.start_conversation(
                user_id="test_user",
                initial_message="",
                language="en"
            )
        
        assert "message" in str(exc_info.value).lower()
    
    def test_invalid_language_handling(self, chat_service):
        """Test handling of unsupported languages"""
        with pytest.raises(ValueError) as exc_info:
            chat_service.start_conversation(
                user_id="test_user",
                initial_message="Test message",
                language="fr"  # Unsupported language
            )
        
        assert "language" in str(exc_info.value).lower()
    
    def test_service_failure_recovery(self, chat_service):
        """Test graceful handling of service failures"""
        # Test should handle temporary service unavailability
        # This is more of an integration test to ensure proper error propagation
        
        try:
            response = chat_service.start_conversation(
                user_id="failure_test_user",
                initial_message="My car has brake problems",
                language="en"
            )
            
            # Should either succeed or fail gracefully
            assert isinstance(response, dict)
            
        except Exception as e:
            # Should provide informative error messages
            assert str(e) is not None and len(str(e)) > 0


class TestChatServiceContextManagement:
    """Test conversation context management and retrieval"""
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_conversation_history_retrieval(self, chat_service):
        """Test retrieving conversation history with proper context"""
        # Start conversation
        response = chat_service.start_conversation(
            user_id="history_test_user",
            initial_message="My Ford F-150 truck has steering issues",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Add follow-up messages
        for i in range(3):
            chat_service.process_message(
                user_id="history_test_user",
                conversation_id=conversation_id,
                message=f"Additional steering question {i+1}",
                language="en"
            )
        
        # Retrieve conversation history
        history = chat_service.get_conversation_history(conversation_id)
        
        assert isinstance(history, list)
        assert len(history) >= 4  # Initial + 3 follow-ups + responses
        
        # Should maintain chronological order
        assert history[0]['role'] == 'user'
        assert 'ford' in history[0]['content'].lower() or 'f-150' in history[0]['content'].lower()
    
    def test_user_conversation_listing(self, chat_service):
        """Test listing all conversations for a user"""
        user_id = "conversation_list_test_user"
        
        # Create multiple conversations
        conv1 = chat_service.start_conversation(
            user_id=user_id,
            initial_message="First conversation about brakes",
            language="en"
        )
        
        conv2 = chat_service.start_conversation(
            user_id=user_id,
            initial_message="Second conversation about engine",
            language="en"
        )
        
        # Get user conversations
        conversations = chat_service.get_user_conversations(user_id)
        
        assert isinstance(conversations, list)
        assert len(conversations) >= 2
        
        # Should include both conversation IDs
        conversation_ids = [conv['id'] for conv in conversations]
        assert conv1['conversation_id'] in conversation_ids
        assert conv2['conversation_id'] in conversation_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 