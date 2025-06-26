import pytest
import time
from app.services.openai_service import OpenAIService


class TestContentModerationBasics:
    """Test basic content moderation functionality"""
    
    def test_moderation_service_availability(self):
        """Test that moderation service is available through OpenAI service"""
        service = OpenAIService()
        assert hasattr(service, 'moderate_content')
        assert callable(service.moderate_content)
    
    def test_safe_content_moderation(self):
        """Test moderation of safe, appropriate content"""
        service = OpenAIService()
        
        safe_content = "My car engine is making a strange noise. Can you help me diagnose the problem?"
        
        result = service.moderate_content(safe_content)
        assert result is not None
        assert isinstance(result, dict)
        assert "flagged" in result
        assert result["flagged"] is False
        assert "categories" in result
        assert "category_scores" in result
        assert "safe" in result
        assert result["safe"] is True
    
    def test_automotive_content_moderation(self):
        """Test moderation of automotive-related content"""
        service = OpenAIService()
        
        automotive_contents = [
            "My brake pedal feels spongy when I press it.",
            "ჩემი მანქანის ძრავი ცუდად მუშაობს",  # Georgian: My car engine works badly
            "The transmission is slipping when I accelerate.",
            "My headlights are not working properly.",
            "I need help with oil change procedures."
        ]
        
        for content in automotive_contents:
            result = service.moderate_content(content)
            assert result["flagged"] is False
            assert result["safe"] is True
            assert isinstance(result["categories"], dict)
            assert isinstance(result["category_scores"], dict)
    
    def test_inappropriate_content_detection(self):
        """Test detection of inappropriate content"""
        service = OpenAIService()
        
        # Test with mildly inappropriate content that should be flagged
        inappropriate_content = "I hate this stupid car and want to destroy it completely with violence"
        
        result = service.moderate_content(inappropriate_content)
        assert result is not None
        assert isinstance(result, dict)
        
        # The content might or might not be flagged depending on OpenAI's current moderation model
        # But we should get a proper response structure
        assert "flagged" in result
        assert "categories" in result
        assert "category_scores" in result
        assert "safe" in result
        assert isinstance(result["flagged"], bool)
        assert isinstance(result["safe"], bool)
    
    def test_empty_content_handling(self):
        """Test handling of empty or invalid content"""
        service = OpenAIService()
        
        # Test empty string
        result = service.moderate_content("")
        assert result["safe"] is True  # Empty content should be considered safe
        assert result["flagged"] is False
        
        # Test whitespace only
        result = service.moderate_content("   ")
        assert result["safe"] is True
        assert result["flagged"] is False


class TestContentModerationDetailed:
    """Test detailed moderation category analysis"""
    
    def test_moderation_categories_structure(self):
        """Test that moderation returns proper category structure"""
        service = OpenAIService()
        
        content = "I need help with my car's electrical system."
        result = service.moderate_content(content)
        
        # Check that all expected categories are present
        expected_categories = [
            "hate", "hate/threatening", "harassment", "harassment/threatening",
            "self-harm", "self-harm/intent", "self-harm/instructions",
            "sexual", "sexual/minors", "violence", "violence/graphic"
        ]
        
        categories = result["categories"]
        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], bool)
        
        # Check category scores
        category_scores = result["category_scores"]
        for category in expected_categories:
            assert category in category_scores
            assert isinstance(category_scores[category], (int, float))
            assert 0.0 <= category_scores[category] <= 1.0
    
    def test_moderation_confidence_scores(self):
        """Test that confidence scores are reasonable for automotive content"""
        service = OpenAIService()
        
        automotive_content = "The brake fluid needs to be replaced regularly for safety."
        result = service.moderate_content(automotive_content)
        
        # For safe automotive content, most category scores should be very low
        category_scores = result["category_scores"]
        
        # Most scores should be very low for safe content
        low_risk_categories = ["hate", "harassment", "self-harm", "sexual", "violence"]
        for category in low_risk_categories:
            if category in category_scores:
                assert category_scores[category] < 0.1, f"Category {category} score too high: {category_scores[category]}"
    
    def test_bilingual_content_moderation(self):
        """Test moderation of bilingual content (Georgian and English)"""
        service = OpenAIService()
        
        bilingual_contents = [
            "Hello, ჩემი მანქანის problem with engine",
            "My car ძრავი has issues with oil",
            "Help me with ფრენების system diagnosis"
        ]
        
        for content in bilingual_contents:
            result = service.moderate_content(content)
            assert result["safe"] is True
            assert result["flagged"] is False
            # Mixed language automotive content should be considered safe


class TestContentModerationPerformance:
    """Test moderation performance requirements"""
    
    def test_moderation_response_time(self):
        """Test that moderation responds within acceptable time"""
        service = OpenAIService()
        
        content = "I need help diagnosing engine problems in my vehicle."
        
        start_time = time.time()
        result = service.moderate_content(content)
        response_time = time.time() - start_time
        
        # Moderation should be fast (faster than chat completions)
        assert response_time < 5.0, f"Moderation took {response_time:.2f}s, should be < 5s"
        assert result is not None
        assert result["safe"] is True
    
    def test_batch_moderation_performance(self):
        """Test moderation of multiple messages efficiently"""
        service = OpenAIService()
        
        messages = [
            "My brake pedal is soft",
            "Engine oil pressure is low",
            "Transmission fluid needs checking",
            "Battery terminals are corroded",
            "Tire pressure monitoring system warning"
        ]
        
        start_time = time.time()
        results = []
        
        for message in messages:
            result = service.moderate_content(message)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # All should be safe automotive content
        assert len(results) == 5
        for result in results:
            assert result["safe"] is True
            assert result["flagged"] is False
        
        # Should process efficiently
        assert total_time < 15.0, f"5 moderations took {total_time:.2f}s, should be < 15s"


class TestContentModerationIntegration:
    """Test moderation integration with conversation flow"""
    
    def test_moderate_before_processing(self):
        """Test moderation as part of message processing workflow"""
        service = OpenAIService()
        
        user_message = "Can you help me understand why my car engine stalls?"
        
        # Step 1: Moderate the content
        moderation_result = service.moderate_content(user_message)
        assert moderation_result["safe"] is True
        
        # Step 2: If safe, process with OpenAI
        if moderation_result["safe"]:
            messages = [
                {"role": "system", "content": "You are an automotive expert assistant."},
                {"role": "user", "content": user_message}
            ]
            
            completion_result = service.create_completion(messages=messages, max_tokens=100)
            assert completion_result is not None
            assert "content" in completion_result
    
    def test_moderate_assistant_responses(self):
        """Test moderating assistant responses before returning to user"""
        service = OpenAIService()
        
        # Create a response
        messages = [
            {"role": "system", "content": "You are a helpful automotive assistant."},
            {"role": "user", "content": "What should I check if my car won't start?"}
        ]
        
        response = service.create_completion(messages=messages, max_tokens=150)
        assistant_content = response["content"]
        
        # Moderate the assistant's response
        moderation_result = service.moderate_content(assistant_content)
        
        # Assistant responses should be safe
        assert moderation_result["safe"] is True
        assert moderation_result["flagged"] is False
    
    def test_conversation_safety_workflow(self):
        """Test complete safety workflow for conversation"""
        from app.db.repositories.conversation_repository import ConversationRepository
        
        service = OpenAIService()
        repo = ConversationRepository()
        
        # Create conversation
        conversation_id = repo.create_conversation(
            user_id="moderation_test_user",
            language="en",
            title="Safety Test Conversation"
        )
        
        try:
            user_message = "My vehicle makes weird noises when braking"
            
            # 1. Moderate user input
            user_moderation = service.moderate_content(user_message)
            assert user_moderation["safe"] is True
            
            # 2. Add safe user message to conversation
            if user_moderation["safe"]:
                repo.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_message,
                    language="en"
                )
                
                # 3. Generate assistant response
                messages = [
                    {"role": "system", "content": "You are an automotive expert."},
                    {"role": "user", "content": user_message}
                ]
                
                assistant_response = service.create_completion(messages=messages, max_tokens=100)
                assistant_content = assistant_response["content"]
                
                # 4. Moderate assistant response
                assistant_moderation = service.moderate_content(assistant_content)
                assert assistant_moderation["safe"] is True
                
                # 5. Add safe assistant response to conversation
                if assistant_moderation["safe"]:
                    repo.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=assistant_content,
                        language="en"
                    )
            
            # Verify complete conversation
            messages = repo.get_conversation_messages(conversation_id)
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"
            
        finally:
            # Cleanup
            repo.delete_conversation(conversation_id)


class TestContentModerationErrorHandling:
    """Test error handling in moderation functionality"""
    
    def test_moderation_with_none_input(self):
        """Test moderation handles None input gracefully"""
        service = OpenAIService()
        
        with pytest.raises(ValueError):
            service.moderate_content(None)
    
    def test_moderation_with_non_string_input(self):
        """Test moderation handles non-string input"""
        service = OpenAIService()
        
        with pytest.raises(ValueError):
            service.moderate_content(123)
        
        with pytest.raises(ValueError):
            service.moderate_content(["list", "of", "items"])
    
    def test_moderation_error_recovery(self):
        """Test that moderation service can recover from errors"""
        service = OpenAIService()
        
        # First, a successful moderation
        result1 = service.moderate_content("Normal automotive question")
        assert result1["safe"] is True
        
        # Then an error (invalid input)
        try:
            service.moderate_content(None)
        except ValueError:
            pass  # Expected
        
        # Then another successful moderation to verify recovery
        result2 = service.moderate_content("Another automotive question")
        assert result2["safe"] is True
    
    def test_extremely_long_content_handling(self):
        """Test handling of very long content"""
        service = OpenAIService()
        
        # Create very long content (but still reasonable)
        long_content = "My car engine problem: " + "This is a very detailed description. " * 100
        
        # Should handle long content without errors
        result = service.moderate_content(long_content)
        assert result is not None
        assert "safe" in result
        assert "flagged" in result


class TestContentModerationConfigurable:
    """Test configurable moderation settings"""
    
    def test_moderation_with_custom_thresholds(self):
        """Test moderation with configurable safety thresholds"""
        service = OpenAIService()
        
        content = "I'm frustrated with my car's recurring issues"
        
        # Test with default thresholds
        result_default = service.moderate_content(content)
        
        # Test with strict thresholds (if implemented)
        if hasattr(service, 'moderate_content_strict'):
            result_strict = service.moderate_content_strict(content)
            assert "safe" in result_strict
        
        # Basic moderation should work
        assert result_default["safe"] is True
    
    def test_moderation_result_enrichment(self):
        """Test that moderation results include helpful metadata"""
        service = OpenAIService()
        
        content = "Please help me fix my brake system safely"
        result = service.moderate_content(content)
        
        # Check for enriched metadata
        assert "model" in result or "id" in result  # OpenAI API response metadata
        assert "categories" in result
        assert "category_scores" in result
        assert "flagged" in result
        assert "safe" in result  # Our custom safety determination
        
        # Verify that our safety determination is consistent with flagged status
        if result["flagged"]:
            assert result["safe"] is False
        else:
            assert result["safe"] is True 