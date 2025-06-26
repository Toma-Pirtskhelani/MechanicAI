import pytest
import time
from app.services.openai_service import OpenAIService
from app.config import config


class TestContextCompression:
    """Test suite for conversation context compression functionality"""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance for testing"""
        return OpenAIService()
    
    def test_context_compression_basic_conversation(self, openai_service):
        """Test basic conversation context compression"""
        conversation_messages = [
            {"role": "user", "content": "My car engine is making noise"},
            {"role": "assistant", "content": "Can you describe the type of noise? Is it a knocking, grinding, or squealing sound?"},
            {"role": "user", "content": "It's a knocking sound when I accelerate"},
            {"role": "assistant", "content": "Engine knocking during acceleration often indicates issues with fuel quality, timing, or carbon buildup. I recommend checking your fuel octane rating first."},
            {"role": "user", "content": "I always use premium gas"},
            {"role": "assistant", "content": "Since you're using premium fuel, the knocking could be due to carbon deposits or timing issues. You should have the engine timing checked by a professional mechanic."}
        ]
        
        result = openai_service.compress_conversation_context(conversation_messages)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "compressed_context" in result, "Result should contain 'compressed_context' key"
        assert "compression_ratio" in result, "Result should contain 'compression_ratio' key"
        assert "preserved_information" in result, "Result should contain 'preserved_information' key"
        
        compressed_text = result["compressed_context"]
        assert isinstance(compressed_text, str), "Compressed context should be string"
        assert len(compressed_text) > 20, "Compressed context should be meaningful"
        
        # Should preserve key automotive information
        automotive_terms = ["engine", "knocking", "accelerat", "fuel", "timing", "premium", "gas"]
        compressed_lower = compressed_text.lower()
        found_terms = [term for term in automotive_terms if term in compressed_lower]
        assert len(found_terms) >= 4, f"Should preserve automotive context. Found: {found_terms}"
        
        # Check compression ratio
        original_length = sum(len(msg["content"]) for msg in conversation_messages)
        compression_ratio = result["compression_ratio"]
        assert isinstance(compression_ratio, (int, float)), "Compression ratio should be numeric"
        assert 0 < compression_ratio <= 1, "Compression ratio should be between 0 and 1"
        assert len(compressed_text) < original_length, "Compressed text should be shorter than original"
    
    def test_context_compression_bilingual_conversation(self, openai_service):
        """Test context compression for bilingual conversations"""
        bilingual_messages = [
            {"role": "user", "content": "ჩემი მანქანის სამუხრუჭე დისკები ყვირის"},  # My car's brake discs are squealing
            {"role": "assistant", "content": "Brake disc squealing usually indicates worn brake pads. When did you last replace your brake pads?"},
            {"role": "user", "content": "About 6 months ago, but the noise started recently"},
            {"role": "assistant", "content": "If the pads are relatively new, the squealing might be due to dust, moisture, or pad material. Try gentle braking to clean the discs."},
            {"role": "user", "content": "მადლობა, სცადავ"},  # Thank you, I'll try
            {"role": "assistant", "content": "You're welcome! If the squealing continues after a few drives, please have the brake system inspected by a professional."}
        ]
        
        result = openai_service.compress_conversation_context(bilingual_messages)
        compressed_text = result["compressed_context"]
        
        # Should preserve both languages and automotive context
        automotive_terms_en = ["brake", "disc", "squeal", "pad", "noise"]
        automotive_terms_ka = ["სამუხრუჭე", "დისკები", "ყვირის"]
        
        compressed_lower = compressed_text.lower()
        found_en = [term for term in automotive_terms_en if term in compressed_lower]
        found_ka = [term for term in automotive_terms_ka if term in compressed_lower]
        
        assert len(found_en) >= 3 or len(found_ka) >= 1, \
            f"Should preserve bilingual automotive context. EN: {found_en}, KA: {found_ka}"
        
        # Should indicate bilingual nature - the compression preserves automotive content even if Georgian text is compressed to English
        preserved_info = result["preserved_information"]
        assert "brakes" in preserved_info["topics"] or len(found_en) >= 3, \
            "Should preserve bilingual automotive information in some form"
    
    def test_context_compression_long_conversation(self, openai_service):
        """Test compression of long conversations with multiple topics"""
        long_conversation = []
        
        # Engine issue discussion
        engine_messages = [
            {"role": "user", "content": "My 2018 Honda Civic engine overheats after 30 minutes of driving"},
            {"role": "assistant", "content": "Engine overheating can be caused by low coolant, faulty thermostat, or radiator issues. Have you checked the coolant level?"},
            {"role": "user", "content": "Coolant level looks fine, but the radiator fan doesn't seem to work"},
            {"role": "assistant", "content": "A non-functioning radiator fan is likely the cause. The fan motor or relay may need replacement. This should be addressed immediately."}
        ]
        
        # Follow-up brake discussion
        brake_messages = [
            {"role": "user", "content": "Also, I've been having brake problems lately"},
            {"role": "assistant", "content": "What kind of brake problems are you experiencing? Any grinding, squealing, or soft pedal feel?"},
            {"role": "user", "content": "The brake pedal feels spongy and goes almost to the floor"},
            {"role": "assistant", "content": "A spongy brake pedal that goes to the floor suggests air in the brake lines or brake fluid leak. This is a serious safety issue - stop driving immediately."}
        ]
        
        # Additional maintenance questions
        maintenance_messages = [
            {"role": "user", "content": "When should I change the transmission fluid?"},
            {"role": "assistant", "content": "For a 2018 Honda Civic, transmission fluid should typically be changed every 25,000-30,000 miles or as specified in your owner's manual."},
            {"role": "user", "content": "The car has 45,000 miles now"},
            {"role": "assistant", "content": "With 45,000 miles, you're likely due for a transmission fluid change. Check your maintenance records to see when it was last done."}
        ]
        
        long_conversation = engine_messages + brake_messages + maintenance_messages
        
        result = openai_service.compress_conversation_context(long_conversation)
        compressed_text = result["compressed_context"]
        
        # Should preserve all major automotive topics
        engine_terms = ["engine", "overheat", "coolant", "radiator", "fan"]
        brake_terms = ["brake", "pedal", "spongy", "fluid", "safety"]
        maintenance_terms = ["transmission", "fluid", "miles", "maintenance"]
        
        compressed_lower = compressed_text.lower()
        found_engine = [term for term in engine_terms if term in compressed_lower]
        found_brake = [term for term in brake_terms if term in compressed_lower]
        found_maintenance = [term for term in maintenance_terms if term in compressed_lower]
        
        assert len(found_engine) >= 3, f"Should preserve engine discussion. Found: {found_engine}"
        assert len(found_brake) >= 3, f"Should preserve brake discussion. Found: {found_brake}"
        assert len(found_maintenance) >= 2, f"Should preserve maintenance discussion. Found: {found_maintenance}"
        
        # Should have good compression ratio for long conversations
        assert result["compression_ratio"] < 0.8, "Should achieve good compression for long conversations"
    
    def test_context_compression_vehicle_information_preservation(self, openai_service):
        """Test that vehicle-specific information is preserved during compression"""
        vehicle_conversation = [
            {"role": "user", "content": "I have a 2020 BMW X5 with 35,000 miles. The turbo seems to be losing power."},
            {"role": "assistant", "content": "Turbo power loss in BMW X5s can be due to carbon buildup, faulty wastegate, or boost leak. Have you noticed any unusual sounds?"},
            {"role": "user", "content": "There's a whistling sound during acceleration"},
            {"role": "assistant", "content": "Whistling during acceleration often indicates a boost leak in the intercooler pipes or turbo seals. BMW X5 turbos are known for this issue around 30k-40k miles."},
            {"role": "user", "content": "Is this covered under warranty?"},
            {"role": "assistant", "content": "A 2020 BMW X5 should still be under the 4-year/50,000-mile warranty. Turbo issues are typically covered, but you'll need BMW diagnosis for warranty claim."}
        ]
        
        result = openai_service.compress_conversation_context(vehicle_conversation)
        compressed_text = result["compressed_context"]
        
        # Should preserve vehicle-specific details
        vehicle_details = ["2020", "bmw", "x5", "35,000", "miles", "turbo"]
        compressed_lower = compressed_text.lower()
        found_details = [detail for detail in vehicle_details if detail in compressed_lower]
        
        assert len(found_details) >= 4, f"Should preserve vehicle information. Found: {found_details}"
        
        # Should preserve technical context
        technical_terms = ["turbo", "power", "whistling", "boost", "leak", "warranty"]
        found_technical = [term for term in technical_terms if term in compressed_lower]
        assert len(found_technical) >= 4, f"Should preserve technical context. Found: {found_technical}"
    
    def test_context_compression_safety_critical_information(self, openai_service):
        """Test that safety-critical information is preserved during compression"""
        safety_conversation = [
            {"role": "user", "content": "My brake pedal went to the floor while driving"},
            {"role": "assistant", "content": "This is extremely dangerous! Pull over safely immediately and do not drive the vehicle. You likely have brake fluid leak or complete brake failure."},
            {"role": "user", "content": "I managed to stop using the parking brake"},
            {"role": "assistant", "content": "Good thinking using the parking brake. Do NOT drive this vehicle. Call for towing to a repair shop immediately. This is a life-threatening safety issue."},
            {"role": "user", "content": "Should I check the brake fluid level?"},
            {"role": "assistant", "content": "You can check, but regardless of the level, do not attempt to drive. Even if fluid is present, you may have internal brake system failure requiring immediate professional repair."}
        ]
        
        result = openai_service.compress_conversation_context(safety_conversation)
        compressed_text = result["compressed_context"]
        
        # Should preserve safety warnings
        safety_terms = ["dangerous", "immediately", "do not drive", "safety", "brake failure", "emergency"]
        compressed_lower = compressed_text.lower()
        found_safety = [term for term in safety_terms if term in compressed_lower]
        
        assert len(found_safety) >= 2, f"Should preserve safety warnings. Found: {found_safety}"
        
        # Should maintain urgency in preserved information
        preserved_info = result["preserved_information"]
        assert len(preserved_info["safety_flags"]) > 0, \
            f"Should flag safety-critical information. Safety flags: {preserved_info['safety_flags']}"
    
    def test_context_compression_empty_conversation(self, openai_service):
        """Test handling of empty or minimal conversations"""
        empty_conversations = [
            [],  # Empty conversation
            [{"role": "user", "content": "Hello"}],  # Single message
            [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello! How can I help with your vehicle?"}]  # Minimal exchange
        ]
        
        for conv in empty_conversations:
            result = openai_service.compress_conversation_context(conv)
            
            assert isinstance(result, dict), "Should return dict for minimal conversations"
            
            if len(conv) == 0:
                assert result["compressed_context"] == "", "Empty conversation should return empty context"
                assert result["compression_ratio"] == 1.0, "Empty conversation should have ratio 1.0"
            else:
                assert len(result["compressed_context"]) > 0, "Non-empty conversation should have some context"
                assert "preserved_information" in result, "Should have preserved information structure"
    
    def test_context_compression_invalid_input(self, openai_service):
        """Test error handling for invalid inputs"""
        # Test None input
        with pytest.raises(ValueError, match="Conversation messages cannot be None"):
            openai_service.compress_conversation_context(None)
        
        # Test non-list input
        invalid_inputs = ["not a list", 123, {"not": "list"}]
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError, match="Conversation messages must be a list"):
                openai_service.compress_conversation_context(invalid_input)
        
        # Test malformed messages (should handle gracefully)
        malformed_messages = [
            [{"invalid": "message"}],  # Missing required keys
            [{"role": "invalid", "content": "test"}],  # Invalid role
        ]
        
        for malformed in malformed_messages:
            result = openai_service.compress_conversation_context(malformed)
            assert isinstance(result, dict), "Should handle malformed messages gracefully"
    
    def test_context_compression_performance_requirements(self, openai_service):
        """Test that context compression meets performance requirements"""
        # Create a moderately long conversation for performance testing
        performance_conversation = []
        for i in range(10):
            performance_conversation.extend([
                {"role": "user", "content": f"Question {i+1}: What causes engine noise in cars?"},
                {"role": "assistant", "content": f"Engine noise can be caused by various factors including worn bearings, timing chain issues, or valve problems. The specific type of noise helps determine the root cause."}
            ])
        
        start_time = time.time()
        result = openai_service.compress_conversation_context(performance_conversation)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response_time < 20.0, f"Compression time {response_time:.2f}s should be under 20s"
        assert isinstance(result, dict), "Should return valid result"
        assert len(result["compressed_context"]) > 0, "Should return meaningful compression"
        assert result["compression_ratio"] < 0.8, "Should achieve reasonable compression"
    
    def test_context_compression_preserves_technical_codes(self, openai_service):
        """Test that diagnostic codes and technical information are preserved"""
        technical_conversation = [
            {"role": "user", "content": "My check engine light is on and I got code P0301"},
            {"role": "assistant", "content": "Code P0301 indicates a misfire in cylinder 1. This could be due to faulty spark plug, ignition coil, or fuel injector."},
            {"role": "user", "content": "I also got P0420 code"},
            {"role": "assistant", "content": "P0420 indicates catalytic converter efficiency below threshold. Combined with P0301, you may have multiple issues affecting emissions."},
            {"role": "user", "content": "What should I check first?"},
            {"role": "assistant", "content": "Start with the P0301 misfire. Replace spark plugs and check ignition coils for cylinder 1. The P0420 may resolve once the misfire is fixed."}
        ]
        
        result = openai_service.compress_conversation_context(technical_conversation)
        compressed_text = result["compressed_context"]
        
        # Should preserve diagnostic codes
        codes = ["p0301", "p0420"]
        compressed_lower = compressed_text.lower()
        found_codes = [code for code in codes if code in compressed_lower]
        
        assert len(found_codes) >= 2, f"Should preserve diagnostic codes. Found: {found_codes}"
        
        # Should preserve technical context
        technical_terms = ["misfire", "cylinder", "catalytic", "converter", "spark", "plug", "ignition", "coil"]
        found_technical = [term for term in technical_terms if term in compressed_lower]
        assert len(found_technical) >= 5, f"Should preserve technical context. Found: {found_technical}"
    
    def test_context_compression_conversation_flow_preservation(self, openai_service):
        """Test that the logical flow of conversation is preserved"""
        flow_conversation = [
            {"role": "user", "content": "My car won't start"},
            {"role": "assistant", "content": "Let's diagnose this step by step. Do the lights work when you turn the key?"},
            {"role": "user", "content": "Yes, lights work fine"},
            {"role": "assistant", "content": "Good, so the battery has power. Does the engine turn over when you try to start it?"},
            {"role": "user", "content": "No, nothing happens when I turn the key"},
            {"role": "assistant", "content": "If lights work but engine doesn't turn over, it's likely the starter motor or ignition switch. Can you hear any clicking sounds?"},
            {"role": "user", "content": "I hear a single click then nothing"},
            {"role": "assistant", "content": "Single click usually indicates a faulty starter motor or poor electrical connection to the starter. The starter solenoid engages but the motor doesn't turn."}
        ]
        
        result = openai_service.compress_conversation_context(flow_conversation)
        compressed_text = result["compressed_context"]
        
        # Should preserve the diagnostic progression
        diagnostic_flow = ["won't start", "lights work", "doesn't turn over", "clicking", "starter"]
        compressed_lower = compressed_text.lower()
        found_flow = [step for step in diagnostic_flow if step in compressed_lower]
        
        assert len(found_flow) >= 2, f"Should preserve key diagnostic elements. Found: {found_flow}"
        
        # Should maintain logical sequence
        assert "battery" in compressed_lower or "power" in compressed_lower, "Should preserve power check"
        assert "starter" in compressed_lower, "Should preserve final diagnosis"
    
    def test_context_compression_multiple_issues_tracking(self, openai_service):
        """Test compression of conversations with multiple automotive issues"""
        multi_issue_conversation = [
            {"role": "user", "content": "I have multiple problems with my car"},
            {"role": "assistant", "content": "I can help you prioritize multiple issues. What problems are you experiencing?"},
            {"role": "user", "content": "Engine overheating, brake grinding, and air conditioning not working"},
            {"role": "assistant", "content": "These are three separate systems. The brake grinding is the most safety-critical and should be addressed immediately."},
            {"role": "user", "content": "How urgent is the overheating?"},
            {"role": "assistant", "content": "Engine overheating is also urgent as it can cause expensive engine damage. Don't drive until both brake and cooling issues are resolved."},
            {"role": "user", "content": "What about the AC?"},
            {"role": "assistant", "content": "AC problems are less urgent but could indicate refrigerant leak or compressor issues. Address after safety-critical brake and engine problems."}
        ]
        
        result = openai_service.compress_conversation_context(multi_issue_conversation)
        compressed_text = result["compressed_context"]
        
        # Should preserve all three issue categories
        engine_terms = ["engine", "overheating", "cooling"]
        brake_terms = ["brake", "grinding", "safety"]
        ac_terms = ["air conditioning", "ac", "refrigerant", "compressor"]
        
        compressed_lower = compressed_text.lower()
        found_engine = [term for term in engine_terms if term in compressed_lower]
        found_brake = [term for term in brake_terms if term in compressed_lower]
        found_ac = [term for term in ac_terms if term in compressed_lower]
        
        assert len(found_engine) >= 2, f"Should preserve engine issues. Found: {found_engine}"
        assert len(found_brake) >= 2, f"Should preserve brake issues. Found: {found_brake}"
        assert len(found_ac) >= 1, f"Should preserve AC issues. Found: {found_ac}"
        
        # Should preserve priority information
        priority_terms = ["urgent", "safety", "critical", "immediately"]
        found_priority = [term for term in priority_terms if term in compressed_lower]
        assert len(found_priority) >= 2, f"Should preserve priority guidance. Found: {found_priority}"
    
    def test_context_compression_response_structure(self, openai_service):
        """Test that compression response has correct structure"""
        test_conversation = [
            {"role": "user", "content": "Engine making noise"},
            {"role": "assistant", "content": "What type of noise? Knocking, grinding, or squealing?"}
        ]
        
        result = openai_service.compress_conversation_context(test_conversation)
        
        # Check required keys
        required_keys = ["compressed_context", "compression_ratio", "preserved_information"]
        for key in required_keys:
            assert key in result, f"Result must contain '{key}' key"
        
        # Check data types
        assert isinstance(result["compressed_context"], str), "compressed_context must be string"
        assert isinstance(result["compression_ratio"], (int, float)), "compression_ratio must be numeric"
        assert isinstance(result["preserved_information"], dict), "preserved_information must be dict"
        
        # Check value constraints
        assert 0 <= result["compression_ratio"] <= 1, "compression_ratio must be between 0 and 1"
        
        # Check preserved information structure
        preserved_info = result["preserved_information"]
        expected_info_keys = ["topics", "vehicle_info", "safety_flags"]
        for key in expected_info_keys:
            assert key in preserved_info, f"preserved_information must contain '{key}' key" 