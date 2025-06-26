import pytest
import time
from app.services.openai_service import OpenAIService
from app.config import config


class TestExpertResponseGeneration:
    """Test suite for expert automotive response generation functionality"""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance for testing"""
        return OpenAIService()
    
    def test_expert_response_basic_engine_problem_english(self, openai_service):
        """Test expert response for basic engine problems in English"""
        user_query = "My car engine is making a strange knocking noise when I accelerate"
        
        result = openai_service.generate_expert_response(user_query)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "response" in result, "Result should contain 'response' key"
        assert "confidence" in result, "Result should contain 'confidence' key"
        assert "language" in result, "Result should contain 'language' key"
        
        response_text = result["response"]
        assert isinstance(response_text, str), "Response should be string"
        assert len(response_text) > 50, "Response should be detailed (>50 chars)"
        
        # Check for professional automotive terminology
        automotive_terms = ["engine", "knock", "fuel", "oil", "cylinder", "compression", "timing"]
        response_lower = response_text.lower()
        found_terms = [term for term in automotive_terms if term in response_lower]
        assert len(found_terms) >= 2, f"Response should contain automotive terms. Found: {found_terms}"
        
        # Check confidence and language detection
        assert isinstance(result["confidence"], (int, float)), "Confidence should be numeric"
        assert 0 <= result["confidence"] <= 1, "Confidence should be between 0 and 1"
        assert result["language"] in ["en", "ka", "mixed"], "Language should be detected"
    
    def test_expert_response_basic_brake_problem_georgian(self, openai_service):
        """Test expert response for brake problems in Georgian"""
        user_query = "ჩემი მანქანის სამუხრუჭე დისკები ყვირის როცა ვჩერდები"  # My car's brake discs squeal when I stop
        
        result = openai_service.generate_expert_response(user_query)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        response_text = result["response"]
        
        # Response should be substantial and professional
        assert len(response_text) > 50, "Georgian response should be detailed"
        
        # Should contain Georgian automotive advice or English with Georgian context
        georgian_terms = ["სამუხრუჭე", "დისკი", "ბალიშები", "მანქანა", "რემონტი"]
        english_terms = ["brake", "disc", "pad", "wear", "rotor", "check"]
        
        response_lower = response_text.lower()
        found_georgian = [term for term in georgian_terms if term in response_lower]
        found_english = [term for term in english_terms if term in response_lower]
        
        # Should have automotive content in either language
        assert len(found_georgian) >= 1 or len(found_english) >= 2, \
            f"Should contain automotive terms. Georgian: {found_georgian}, English: {found_english}"
    
    def test_expert_response_transmission_problem(self, openai_service):
        """Test expert response for transmission issues"""
        user_query = "My transmission is slipping when shifting from 2nd to 3rd gear"
        
        result = openai_service.generate_expert_response(user_query)
        response_text = result["response"]
        
        # Should address transmission-specific issues
        transmission_terms = ["transmission", "gear", "shift", "fluid", "clutch", "torque", "slip"]
        response_lower = response_text.lower()
        found_terms = [term for term in transmission_terms if term in response_lower]
        
        assert len(found_terms) >= 3, f"Should contain transmission terminology. Found: {found_terms}"
        assert len(response_text) > 100, "Transmission advice should be detailed"
    
    def test_expert_response_electrical_problem(self, openai_service):
        """Test expert response for electrical issues"""
        user_query = "My car won't start, lights work but engine doesn't turn over"
        
        result = openai_service.generate_expert_response(user_query)
        response_text = result["response"]
        
        # Should address electrical system diagnostics
        electrical_terms = ["battery", "starter", "alternator", "electrical", "ignition", "voltage", "connection"]
        response_lower = response_text.lower()
        found_terms = [term for term in electrical_terms if term in response_lower]
        
        assert len(found_terms) >= 3, f"Should contain electrical terminology. Found: {found_terms}"
        
        # Should provide diagnostic steps
        diagnostic_indicators = ["check", "test", "voltage", "connection", "battery", "starter"]
        found_diagnostic = [term for term in diagnostic_indicators if term in response_lower]
        assert len(found_diagnostic) >= 2, "Should provide diagnostic guidance"
    
    def test_expert_response_with_vehicle_context(self, openai_service):
        """Test expert response when vehicle details are provided"""
        user_query = "2018 Toyota Camry, 45,000 miles - engine overheating after 30 minutes of driving"
        context = {
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_year": "2018",
            "mileage": "45,000"
        }
        
        result = openai_service.generate_expert_response(user_query, context=context)
        response_text = result["response"]
        
        # Should reference the specific vehicle
        assert "toyota" in response_text.lower() or "camry" in response_text.lower(), \
            "Should reference specific vehicle"
        
        # Should address overheating issues
        cooling_terms = ["coolant", "radiator", "thermostat", "fan", "temperature", "overheat"]
        response_lower = response_text.lower()
        found_terms = [term for term in cooling_terms if term in response_lower]
        
        assert len(found_terms) >= 3, f"Should contain cooling system terminology. Found: {found_terms}"
    
    def test_expert_response_safety_considerations(self, openai_service):
        """Test that expert responses include appropriate safety warnings"""
        dangerous_queries = [
            "My brakes are completely gone, how can I stop the car?",
            "Smoke is coming from under the hood while driving",
            "My steering wheel locked up while driving"
        ]
        
        for query in dangerous_queries:
            result = openai_service.generate_expert_response(query)
            response_text = result["response"].lower()
            
            # Should include safety warnings
            safety_indicators = ["safe", "danger", "immediately", "stop", "professional", "mechanic", "emergency"]
            found_safety = [term for term in safety_indicators if term in response_text]
            
            assert len(found_safety) >= 2, f"Should include safety warnings for: {query}. Found: {found_safety}"
    
    def test_expert_response_professional_tone(self, openai_service):
        """Test that responses maintain professional, helpful tone"""
        queries = [
            "I don't know anything about cars, please help",
            "This is really urgent, my car is broken",
            "Can you fix my car problem quickly?"
        ]
        
        for query in queries:
            result = openai_service.generate_expert_response(query)
            response_text = result["response"]
            
            # Should be professional and helpful
            assert len(response_text) > 80, "Should provide detailed professional response"
            
            # Should not be dismissive or overly technical without explanation
            response_lower = response_text.lower()
            helpful_indicators = ["help", "understand", "check", "step", "recommend", "suggest"]
            found_helpful = [term for term in helpful_indicators if term in response_lower]
            
            assert len(found_helpful) >= 2, f"Should be helpful and professional. Found: {found_helpful}"
    
    def test_expert_response_with_conversation_history(self, openai_service):
        """Test expert response with previous conversation context"""
        conversation_history = [
            {"role": "user", "content": "My car is making noise"},
            {"role": "assistant", "content": "Can you describe the type of noise and when it occurs?"},
            {"role": "user", "content": "It's a grinding sound when I brake"}
        ]
        
        current_query = "How urgent is this problem?"
        
        result = openai_service.generate_expert_response(
            current_query, 
            conversation_history=conversation_history
        )
        response_text = result["response"]
        
        # Should reference the brake grinding issue from history
        brake_terms = ["brake", "grinding", "urgent", "safety", "pad", "rotor"]
        response_lower = response_text.lower()
        found_terms = [term for term in brake_terms if term in response_lower]
        
        assert len(found_terms) >= 3, f"Should reference conversation context. Found: {found_terms}"
        
        # Should address urgency of brake problems
        urgency_indicators = ["urgent", "immediate", "soon", "safety", "danger"]
        found_urgency = [term for term in urgency_indicators if term in response_lower]
        assert len(found_urgency) >= 1, "Should address urgency of brake grinding"
    
    def test_expert_response_technical_diagnostic_codes(self, openai_service):
        """Test expert response for OBD-II diagnostic codes"""
        user_query = "My car is showing error code P0301, what does this mean?"
        
        result = openai_service.generate_expert_response(user_query)
        response_text = result["response"]
        
        # Should explain the diagnostic code
        diagnostic_terms = ["p0301", "misfire", "cylinder", "ignition", "fuel", "compression", "diagnostic"]
        response_lower = response_text.lower()
        found_terms = [term for term in diagnostic_terms if term in response_lower]
        
        assert len(found_terms) >= 4, f"Should explain diagnostic code. Found: {found_terms}"
        assert "cylinder" in response_lower, "Should mention cylinder-specific issue"
    
    def test_expert_response_maintenance_advice(self, openai_service):
        """Test expert response for maintenance-related queries"""
        maintenance_queries = [
            "When should I change my oil?",
            "How often should I replace brake pads?",
            "What's the recommended tire rotation schedule?"
        ]
        
        for query in maintenance_queries:
            result = openai_service.generate_expert_response(query)
            response_text = result["response"]
            
            # Should provide specific maintenance guidance
            maintenance_indicators = ["mile", "month", "time", "schedule", "recommend", "replace", "check"]
            response_lower = response_text.lower()
            found_indicators = [term for term in maintenance_indicators if term in response_lower]
            
            assert len(found_indicators) >= 3, f"Should provide maintenance guidance for: {query}"
            assert len(response_text) > 80, "Maintenance advice should be detailed"
    
    def test_expert_response_performance_requirements(self, openai_service):
        """Test that expert response generation meets performance requirements"""
        test_queries = [
            "Engine noise when accelerating",
            "Brake problems",
            "ჩემი მანქანის პრობლემა",  # Georgian: My car's problem
            "Transmission issues"
        ]
        
        for query in test_queries:
            start_time = time.time()
            result = openai_service.generate_expert_response(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response_time < 30.0, f"Response time {response_time:.2f}s should be under 30s for: {query}"
            assert isinstance(result, dict), "Should return valid result"
            assert len(result["response"]) > 30, "Should return substantial response"
    
    def test_expert_response_error_handling(self, openai_service):
        """Test error handling for invalid inputs"""
        # Test None input
        with pytest.raises(ValueError, match="Query cannot be None"):
            openai_service.generate_expert_response(None)
        
        # Test non-string input
        invalid_inputs = [123, ["list"], {"dict": "value"}, True]
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError, match="Query must be a string"):
                openai_service.generate_expert_response(invalid_input)
        
        # Test empty string handling
        result = openai_service.generate_expert_response("")
        assert "response" in result, "Should handle empty strings gracefully"
        assert len(result["response"]) > 0, "Should provide some response for empty input"
    
    def test_expert_response_consistency(self, openai_service):
        """Test that similar queries get consistent expert advice"""
        similar_queries = [
            "Car won't start in the morning",
            "Engine won't turn over when I try to start",
            "Having trouble starting my vehicle"
        ]
        
        responses = []
        for query in similar_queries:
            result = openai_service.generate_expert_response(query)
            responses.append(result)
        
        # All should address starting issues
        starting_terms = ["start", "battery", "ignition", "fuel", "engine", "electrical"]
        
        for i, result in enumerate(responses):
            response_lower = result["response"].lower()
            found_terms = [term for term in starting_terms if term in response_lower]
            assert len(found_terms) >= 3, f"Query {i+1} should address starting issues: {similar_queries[i]}"
        
        # Confidence levels should be reasonably similar
        confidences = [result["confidence"] for result in responses]
        confidence_range = max(confidences) - min(confidences)
        assert confidence_range <= 0.4, f"Confidence range {confidence_range} too wide for similar queries"
    
    def test_expert_response_mixed_language_handling(self, openai_service):
        """Test expert responses for mixed Georgian-English queries"""
        mixed_queries = [
            "My car-ის engine არ მუშაობს properly",  # Mixed: My car's engine doesn't work properly
            "როგორ შევცვალო brake pads-ები?",  # Mixed: How to change brake pads?
            "ჩემი BMW-ის transmission slipping-ს აკეთებს"  # Mixed: My BMW's transmission is slipping
        ]
        
        for query in mixed_queries:
            result = openai_service.generate_expert_response(query)
            response_text = result["response"]
            
            assert len(response_text) > 50, f"Should provide detailed response for mixed language: {query}"
            assert result["language"] in ["en", "ka", "mixed"], "Should detect mixed language"
            
            # Should address the automotive issue regardless of language mixing
            automotive_terms_en = ["engine", "brake", "transmission", "car", "vehicle"]
            automotive_terms_ka = ["მანქანა", "ძრავა", "სამუხრუჭე", "გადაცემათა"]
            
            response_lower = response_text.lower()
            found_en = [term for term in automotive_terms_en if term in response_lower]
            found_ka = [term for term in automotive_terms_ka if term in response_lower]
            
            assert len(found_en) >= 1 or len(found_ka) >= 1, \
                f"Should contain automotive terminology for mixed query: {query}"
    
    def test_expert_response_structure_validation(self, openai_service):
        """Test that expert response has correct structure"""
        query = "Engine overheating problem"
        result = openai_service.generate_expert_response(query)
        
        # Check required keys
        required_keys = ["response", "confidence", "language"]
        for key in required_keys:
            assert key in result, f"Result must contain '{key}' key"
        
        # Check data types
        assert isinstance(result["response"], str), "Response must be string"
        assert isinstance(result["confidence"], (int, float)), "Confidence must be numeric"
        assert isinstance(result["language"], str), "Language must be string"
        
        # Check value ranges and constraints
        assert 0 <= result["confidence"] <= 1, "Confidence must be between 0 and 1"
        assert result["language"] in ["en", "ka", "mixed"], "Language must be valid"
        assert len(result["response"]) > 20, "Response should be substantial (>20 chars)"
    
    def test_expert_response_professional_recommendations(self, openai_service):
        """Test that responses include appropriate professional recommendations"""
        complex_queries = [
            "Multiple warning lights on dashboard and engine running rough",
            "Car pulls to one side when braking and makes grinding noise",
            "Engine overheats and loses power on highway"
        ]
        
        for query in complex_queries:
            result = openai_service.generate_expert_response(query)
            response_text = result["response"].lower()
            
            # Should recommend professional inspection for complex issues
            professional_terms = ["mechanic", "professional", "inspect", "diagnostic", "qualified", "service"]
            found_professional = [term for term in professional_terms if term in response_text]
            
            assert len(found_professional) >= 2, \
                f"Should recommend professional help for complex issue: {query}"
            
            # Should be detailed for complex problems
            assert len(result["response"]) > 150, f"Should provide detailed response for complex query: {query}" 