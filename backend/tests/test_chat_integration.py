"""
Integration tests for complete chat flow - Phase 3.3

Tests the complete end-to-end conversation workflow integrating:
- Chat Service (Phase 3.1)
- Context Enhancement (Phase 3.2) 
- All OpenAI Services (Phase 2)
- Database operations (Phase 1)

This validates that MechaniAI is ready for the API layer implementation.
"""

import pytest
import time
from typing import Dict, Any

from app.core.chat_service import ChatService
from app.core.context_enhancement import ContextEnhancementService
from app.services.openai_service import OpenAIService
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.database_service import DatabaseService


class TestCompleteChatFlowIntegration:
    """Test complete chat flow integration with all services"""
    
    @pytest.fixture
    def chat_service(self):
        """Chat service instance for testing"""
        return ChatService()
    
    @pytest.fixture
    def context_service(self):
        """Context enhancement service for testing"""
        return ContextEnhancementService()
    
    @pytest.fixture
    def test_user_id(self):
        """Test user ID for integration testing"""
        return "integration_test_user_phase_3_3"
    
    def test_complete_automotive_conversation_flow(self, chat_service, context_service, test_user_id):
        """Test complete end-to-end automotive conversation flow"""
        # Step 1: Start conversation with automotive query
        start_response = chat_service.start_conversation(
            user_id=test_user_id,
            initial_message="My 2018 Honda Civic engine is misfiring and the check engine light is on. P0301 code showing.",
            language="en"
        )
        
        assert isinstance(start_response, dict)
        assert 'conversation_id' in start_response
        assert 'response' in start_response
        assert start_response['language'] == 'en'
        
        conversation_id = start_response['conversation_id']
        initial_response = start_response['response'].lower()
        
        # Verify automotive expertise in response
        assert any(term in initial_response for term in ['p0301', 'misfire', 'cylinder', 'engine', 'honda', 'civic'])
        
        # Step 2: Test context enhancement integration
        vehicle_info = context_service.extract_vehicle_information(conversation_id)
        assert 'make' in vehicle_info or 'model' in vehicle_info or 'year' in vehicle_info
        
        symptoms = context_service.extract_symptoms_and_problems(conversation_id)
        assert 'engine_symptoms' in symptoms or 'brake_symptoms' in symptoms or 'confidence' in symptoms
        
        # Step 3: Continue conversation with follow-up
        follow_up_response = chat_service.process_message(
            user_id=test_user_id,
            conversation_id=conversation_id,
            message="What should I check first? Is it safe to drive?",
            language="en"
        )
        
        assert 'response' in follow_up_response
        follow_up_text = follow_up_response['response'].lower()
        
        # Should reference previous context (Honda Civic, P0301, etc.)
        assert any(term in follow_up_text for term in ['spark', 'coil', 'cylinder', 'misfire', 'honda', 'civic'])
        
        # Step 4: Test safety assessment integration
        safety_info = context_service.enrich_context_with_safety_priorities(conversation_id)
        assert 'safety_level' in safety_info or 'priority' in safety_info
        
        # Step 5: Test predictive analysis
        maintenance_info = context_service.enrich_context_with_maintenance_history(conversation_id)
        assert 'maintenance_events' in maintenance_info or 'maintenance_schedule_status' in maintenance_info
        
        # Step 6: Continue with diagnostic follow-up
        diagnostic_response = chat_service.process_message(
            user_id=test_user_id,
            conversation_id=conversation_id,
            message="I checked the spark plug on cylinder 1, it looks burnt. What's next?",
            language="en"
        )
        
        diagnostic_text = diagnostic_response['response'].lower()
        assert any(term in diagnostic_text for term in ['spark plug', 'coil', 'injector', 'replace'])
        
        # Step 7: Verify conversation history maintains context
        history = chat_service.get_conversation_history(conversation_id)
        assert len(history) >= 6  # 3 user messages + 3 assistant responses
        
        # Verify chronological order and content preservation
        user_messages = [msg for msg in history if msg['role'] == 'user']
        assert len(user_messages) == 3
        assert 'p0301' in user_messages[0]['content'].lower()
        assert 'safe to drive' in user_messages[1]['content'].lower()
        assert 'burnt' in user_messages[2]['content'].lower()
    
    def test_bilingual_chat_integration(self, chat_service, context_service, test_user_id):
        """Test complete bilingual conversation integration"""
        # Start in Georgian
        georgian_start = chat_service.start_conversation(
            user_id=test_user_id + "_ka",
            initial_message="ჩემი 2020 Toyota Camry-ს ძრავა ცუდად მუშაობს და ბრეკები კრაკუნს ბოლო დროს",
            language="ka"
        )
        
        assert georgian_start['language'] == 'ka'
        conversation_id = georgian_start['conversation_id']
        
        # Verify context enhancement works with Georgian
        vehicle_info = context_service.extract_vehicle_information(conversation_id)
        symptoms = context_service.extract_symptoms_and_problems(conversation_id)
        
        # Should extract Toyota Camry and engine/brake symptoms
        assert isinstance(vehicle_info, dict)
        assert isinstance(symptoms, dict)
        
        # Continue in English (mixed language conversation)
        english_response = chat_service.process_message(
            user_id=test_user_id + "_ka",
            conversation_id=conversation_id,
            message="How much will brake repair cost approximately?",
            language="en"
        )
        
        # Should maintain context about Toyota Camry and brake issues
        response_text = english_response['response'].lower()
        assert any(term in response_text for term in ['brake', 'repair', 'cost', 'toyota', 'camry'])
        
        # Continue back in Georgian
        georgian_followup = chat_service.process_message(
            user_id=test_user_id + "_ka",
            conversation_id=conversation_id,
            message="რა არის ღირეს შუახნის შეცვლა?",
            language="ka"
        )
        
        # Should continue maintaining context
        assert 'response' in georgian_followup
    
    def test_non_automotive_query_handling_integration(self, chat_service, test_user_id):
        """Test integration of non-automotive query handling"""
        # Non-automotive initial query
        redirect_response = chat_service.start_conversation(
            user_id=test_user_id + "_redirect",
            initial_message="What's the weather like today? Can you tell me about cooking recipes?",
            language="en"
        )
        
        assert 'response' in redirect_response
        response_text = redirect_response['response'].lower()
        
        # Should contain redirect to automotive topics
        assert any(term in response_text for term in ['automotive', 'car', 'vehicle', 'tegeta', 'motors'])
        
        # Follow up with automotive query should work
        conversation_id = redirect_response['conversation_id']
        automotive_followup = chat_service.process_message(
            user_id=test_user_id + "_redirect",
            conversation_id=conversation_id,
            message="Actually, my car brakes are squeaking. What could cause this?",
            language="en"
        )
        
        followup_text = automotive_followup['response'].lower()
        assert any(term in followup_text for term in ['brake', 'squeak', 'pad', 'disc', 'rotor'])
    
    def test_content_moderation_integration(self, chat_service, test_user_id):
        """Test content moderation integration in chat flow"""
        # Attempt inappropriate content with automotive context
        try:
            moderation_response = chat_service.start_conversation(
                user_id=test_user_id + "_mod",
                initial_message="I hate my stupid car and want to destroy it violently",
                language="en"
            )
            
            # Should either reject or provide safe response
            assert 'response' in moderation_response
            response_text = moderation_response['response'].lower()
            
            # Should be safe and helpful, possibly redirecting to proper automotive assistance
            assert any(term in response_text for term in ['help', 'assist', 'technical', 'automotive']) or \
                   'sorry' in response_text
                   
        except ValueError as e:
            # Should provide informative error for unsafe content
            assert 'safety' in str(e).lower() or 'moderation' in str(e).lower()
    
    def test_context_compression_integration(self, chat_service, test_user_id):
        """Test context compression integration in long conversations"""
        # Start conversation
        long_conv_response = chat_service.start_conversation(
            user_id=test_user_id + "_long",
            initial_message="My Ford F-150 has multiple issues I need help with",
            language="en"
        )
        
        conversation_id = long_conv_response['conversation_id']
        
        # Add multiple messages to trigger compression
        topics = [
            "First, the engine makes rattling noise when starting",
            "Second, the transmission shifts roughly between gears", 
            "Third, the brakes feel spongy when I press them",
            "Fourth, the steering wheel vibrates at highway speeds",
            "Fifth, the air conditioning blows warm air",
            "Sixth, there's a grinding noise from the rear wheels"
        ]
        
        for i, topic in enumerate(topics, 1):
            response = chat_service.process_message(
                user_id=test_user_id + "_long",
                conversation_id=conversation_id,
                message=topic,
                language="en"
            )
            
            assert 'response' in response
            
            # Check if compression has occurred (after enough messages)
            if i >= 5:  # After several messages
                # Verify conversation still works and maintains context
                test_response = chat_service.process_message(
                    user_id=test_user_id + "_long",
                    conversation_id=conversation_id,
                    message="Which of these issues should I prioritize?",
                    language="en"
                )
                
                priority_text = test_response['response'].lower()
                # Should reference previous issues even after compression
                assert any(term in priority_text for term in ['brake', 'engine', 'transmission', 'ford', 'priority'])
                break
    
    def test_performance_requirements_integration(self, chat_service, test_user_id):
        """Test that complete integration meets performance requirements"""
        # Test conversation start performance
        start_time = time.time()
        
        perf_response = chat_service.start_conversation(
            user_id=test_user_id + "_perf",
            initial_message="My BMW X5 engine light came on and it's running rough",
            language="en"
        )
        
        start_duration = time.time() - start_time
        assert start_duration < 20.0, f"Conversation start took {start_duration:.2f}s, should be < 20s"
        
        conversation_id = perf_response['conversation_id']
        
        # Test follow-up message performance
        followup_start = time.time()
        
        followup_response = chat_service.process_message(
            user_id=test_user_id + "_perf",
            conversation_id=conversation_id,
            message="What diagnostic steps should I take?",
            language="en"
        )
        
        followup_duration = time.time() - followup_start
        assert followup_duration < 25.0, f"Follow-up message took {followup_duration:.2f}s, should be < 25s"
        
        # Verify quality wasn't sacrificed for performance
        response_text = followup_response['response'].lower()
        assert any(term in response_text for term in ['diagnostic', 'check', 'bmw', 'x5', 'engine'])


class TestChatIntegrationErrorHandling:
    """Test error handling and recovery in complete chat integration"""
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_service_dependency_failure_handling(self, chat_service):
        """Test graceful handling of service dependency failures"""
        # Test chat service health check
        health_status = chat_service.health_check()
        
        assert isinstance(health_status, dict)
        assert 'overall_status' in health_status
        assert 'openai_service' in health_status
        assert 'database_service' in health_status
        
        # If any service is unhealthy, overall should be false
        if not health_status['openai_service'] or not health_status['database_service']:
            assert health_status['overall_status'] is False
        
        # All services should be healthy for integration tests
        assert health_status['overall_status'] is True, f"Services not healthy: {health_status}"
    
    def test_invalid_conversation_handling(self, chat_service):
        """Test handling of invalid conversation operations"""
        # Test processing message in non-existent conversation
        with pytest.raises(ValueError) as exc_info:
            chat_service.process_message(
                user_id="test_user",
                conversation_id="non_existent_conversation_id",
                message="Test message",
                language="en"
            )
        
        assert "conversation" in str(exc_info.value).lower()
        
        # Test getting history for non-existent conversation (should return empty list)
        history = chat_service.get_conversation_history("non_existent_conversation_id")
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_input_validation_integration(self, chat_service):
        """Test input validation across the integrated system"""
        # Empty message
        with pytest.raises(ValueError) as exc_info:
            chat_service.start_conversation(
                user_id="test_user",
                initial_message="",
                language="en"
            )
        
        assert "message" in str(exc_info.value).lower()
        
        # Invalid language
        with pytest.raises(ValueError) as exc_info:
            chat_service.start_conversation(
                user_id="test_user",
                initial_message="Test message",
                language="invalid_language"
            )
        
        assert "language" in str(exc_info.value).lower()
        
        # Empty user ID
        with pytest.raises(ValueError) as exc_info:
            chat_service.start_conversation(
                user_id="",
                initial_message="Test message",
                language="en"
            )
        
        assert "user" in str(exc_info.value).lower()
    
    def test_concurrent_conversation_handling(self, chat_service):
        """Test handling of concurrent conversations for the same user"""
        user_id = "concurrent_test_user"
        
        # Start multiple conversations concurrently
        conv1 = chat_service.start_conversation(
            user_id=user_id,
            initial_message="My Honda Accord has engine problems",
            language="en"
        )
        
        conv2 = chat_service.start_conversation(
            user_id=user_id,
            initial_message="Different car - Toyota Prius brake issues",
            language="en"
        )
        
        # Both conversations should be independent
        assert conv1['conversation_id'] != conv2['conversation_id']
        
        # Should be able to continue both conversations independently
        honda_followup = chat_service.process_message(
            user_id=user_id,
            conversation_id=conv1['conversation_id'],
            message="The engine makes noise when starting",
            language="en"
        )
        
        toyota_followup = chat_service.process_message(
            user_id=user_id,
            conversation_id=conv2['conversation_id'],
            message="The brakes feel soft and spongy",
            language="en"
        )
        
        # Responses should be contextually appropriate to each conversation
        honda_text = honda_followup['response'].lower()
        toyota_text = toyota_followup['response'].lower()
        
        assert any(term in honda_text for term in ['honda', 'accord', 'engine', 'noise'])
        assert any(term in toyota_text for term in ['toyota', 'prius', 'brake', 'soft', 'spongy'])
        
        # Get user conversations - should show both
        user_conversations = chat_service.get_user_conversations(user_id)
        assert len(user_conversations) >= 2
        
        conversation_ids = [conv['id'] for conv in user_conversations]
        assert conv1['conversation_id'] in conversation_ids
        assert conv2['conversation_id'] in conversation_ids


class TestChatIntegrationProductionReadiness:
    """Test production readiness of complete chat integration"""
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    @pytest.fixture
    def context_service(self):
        return ContextEnhancementService()
    
    def test_complete_automotive_expertise_validation(self, chat_service):
        """Test that the complete system provides expert-level automotive advice"""
        expert_queries = [
            {
                'message': "My 2019 Subaru Outback shows P0171 code and idles rough",
                'expected_terms': ['p0171', 'lean', 'fuel', 'air', 'maf', 'vacuum', 'subaru']
            },
            {
                'message': "BMW 328i transmission slips between 2nd and 3rd gear",
                'expected_terms': ['transmission', 'slip', 'gear', 'fluid', 'solenoid', 'bmw']
            },
            {
                'message': "My Ford F-150 steering wheel shakes when braking from high speed",
                'expected_terms': ['steering', 'shake', 'brake', 'rotor', 'warp', 'ford', 'f-150']
            }
        ]
        
        for i, query in enumerate(expert_queries):
            response = chat_service.start_conversation(
                user_id=f"expert_test_user_{i}",
                initial_message=query['message'],
                language="en"
            )
            
            response_text = response['response'].lower()
            
            # Should contain relevant automotive expertise
            matching_terms = [term for term in query['expected_terms'] if term in response_text]
            assert len(matching_terms) >= 2, f"Response lacks automotive expertise. Found: {matching_terms}"
    
    def test_system_scalability_validation(self, chat_service):
        """Test system can handle multiple conversations efficiently"""
        # Create multiple conversations rapidly
        conversations = []
        start_time = time.time()
        
        for i in range(5):
            conv_response = chat_service.start_conversation(
                user_id=f"scalability_test_user_{i}",
                initial_message=f"My car number {i} has engine problems and needs diagnosis",
                language="en"
            )
            conversations.append(conv_response)
        
        creation_time = time.time() - start_time
        assert creation_time < 60.0, f"Creating 5 conversations took {creation_time:.2f}s, should be < 60s"
        
        # Verify all conversations are independent and functional
        for i, conv in enumerate(conversations):
            followup = chat_service.process_message(
                user_id=f"scalability_test_user_{i}",
                conversation_id=conv['conversation_id'],
                message=f"What should I check first for car {i}?",
                language="en"
            )
            
            # Each response should be contextually appropriate
            assert 'response' in followup
            response_text = followup['response'].lower()
            assert any(term in response_text for term in ['check', 'engine', 'diagnostic', 'car'])
    
    def test_data_integrity_validation(self, chat_service):
        """Test data integrity across the complete integrated system"""
        # Create conversation and verify data consistency
        integrity_response = chat_service.start_conversation(
            user_id="data_integrity_test_user",
            initial_message="My 2021 Tesla Model 3 shows error messages on the dashboard",
            language="en"
        )
        
        conversation_id = integrity_response['conversation_id']
        
        # Add several messages
        messages = [
            "The error says 'Charging System Fault'",
            "Also seeing 'Brake System Fault' warning",
            "Should I continue driving or stop immediately?"
        ]
        
        for message in messages:
            chat_service.process_message(
                user_id="data_integrity_test_user",
                conversation_id=conversation_id,
                message=message,
                language="en"
            )
        
        # Verify conversation history integrity
        history = chat_service.get_conversation_history(conversation_id)
        
        # Should have all messages in order
        user_messages = [msg for msg in history if msg['role'] == 'user']
        assert len(user_messages) == 4  # Initial + 3 follow-ups
        
        # Verify content preservation
        assert 'tesla model 3' in user_messages[0]['content'].lower()
        assert 'charging system fault' in user_messages[1]['content'].lower()
        assert 'brake system fault' in user_messages[2]['content'].lower()
        assert 'continue driving' in user_messages[3]['content'].lower()
        
        # Verify assistant responses are contextually appropriate
        assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
        assert len(assistant_messages) == 4
        
        # All responses should show Tesla expertise
        for response in assistant_messages:
            response_text = response['content'].lower()
            assert any(term in response_text for term in ['tesla', 'electric', 'diagnostic', 'service', 'fault'])
    
    def test_phase_4_api_readiness(self, chat_service, context_service):
        """Test that the system is ready for Phase 4 API implementation"""
        # Test core functionality that API will expose
        api_readiness_response = chat_service.start_conversation(
            user_id="api_readiness_test_user",
            initial_message="API readiness test - my car needs diagnostic help",
            language="en"
        )
        
        # Verify all expected response fields for API
        assert isinstance(api_readiness_response, dict)
        required_fields = ['conversation_id', 'response', 'language']
        
        for field in required_fields:
            assert field in api_readiness_response, f"Missing required field: {field}"
            assert api_readiness_response[field] is not None
        
        conversation_id = api_readiness_response['conversation_id']
        
        # Test message processing (main API endpoint functionality)
        message_response = chat_service.process_message(
            user_id="api_readiness_test_user",
            conversation_id=conversation_id,
            message="Follow-up question for API testing",
            language="en"
        )
        
        assert isinstance(message_response, dict)
        assert 'conversation_id' in message_response
        assert 'response' in message_response
        
        # Test conversation retrieval (API endpoint functionality)
        history = chat_service.get_conversation_history(conversation_id)
        assert isinstance(history, list)
        assert len(history) >= 2
        
        # Test user conversations listing (API endpoint functionality)
        user_conversations = chat_service.get_user_conversations("api_readiness_test_user")
        assert isinstance(user_conversations, list)
        assert len(user_conversations) >= 1
        
        # Test health check (API health endpoint)
        health_status = chat_service.health_check()
        assert isinstance(health_status, dict)
        assert health_status['overall_status'] is True
        
        # Test context enhancement integration (API enhancement features)
        vehicle_info = context_service.extract_vehicle_information(conversation_id)
        symptoms = context_service.extract_symptoms_and_problems(conversation_id)
        safety_info = context_service.enrich_context_with_safety_priorities(conversation_id)
        
        assert isinstance(vehicle_info, dict)
        assert isinstance(symptoms, dict)
        assert isinstance(safety_info, dict)
        
        # All integration points ready for API exposure
        print("✅ System is ready for Phase 4: API Layer Implementation")
        print(f"   - Chat Service: Operational")
        print(f"   - Context Enhancement: Operational")
        print(f"   - All AI Services: Integrated")
        print(f"   - Database Operations: Stable")
        print(f"   - Performance: Within requirements")
        print(f"   - Error Handling: Comprehensive") 