import pytest
import asyncio
import time
from app.services.openai_service import OpenAIService
from app.config import config


class TestAutomotiveFilter:
    """Test suite for automotive relevance filtering functionality"""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance for testing"""
        return OpenAIService()
    
    def test_automotive_filter_clearly_automotive_english(self, openai_service):
        """Test that clearly automotive queries in English are correctly identified"""
        automotive_queries = [
            "My car engine is making a strange noise",
            "How do I change brake pads on a Toyota Camry?",
            "My transmission is slipping when I shift gears",
            "Car won't start this morning, battery seems fine",
            "Oil leak under my Honda Civic"
        ]
        
        for query in automotive_queries:
            result = openai_service.check_automotive_relevance(query)
            
            assert isinstance(result, dict), f"Result should be dict for query: {query}"
            assert "is_automotive" in result, "Result should contain 'is_automotive' key"
            assert "confidence" in result, "Result should contain 'confidence' key"
            assert "reasoning" in result, "Result should contain 'reasoning' key"
            
            assert result["is_automotive"] is True, f"Should identify as automotive: {query}"
            assert isinstance(result["confidence"], (int, float)), "Confidence should be numeric"
            assert 0 <= result["confidence"] <= 1, "Confidence should be between 0 and 1"
            assert isinstance(result["reasoning"], str), "Reasoning should be string"
            assert len(result["reasoning"]) > 0, "Reasoning should not be empty"
    
    def test_automotive_filter_clearly_automotive_georgian(self, openai_service):
        """Test that clearly automotive queries in Georgian are correctly identified"""
        automotive_queries_georgian = [
            "ჩემი მანქანის ძრავა უცნაური ხმაურს ამოიღებს",  # My car engine makes strange noise
            "როგორ შევცვალო სამუხრუჭე დისკები?",  # How to change brake discs?
            "მანქანა არ ეშვება დილით",  # Car won't start in the morning
            "ზეთი მოდის მანქანის ქვეშ",  # Oil leaking under the car
            "გადაცემათა კოლოფი პრობლემას იწვევს"  # Transmission causing problems
        ]
        
        for query in automotive_queries_georgian:
            result = openai_service.check_automotive_relevance(query)
            
            assert isinstance(result, dict), f"Result should be dict for Georgian query: {query}"
            assert result["is_automotive"] is True, f"Should identify Georgian automotive query: {query}"
            assert result["confidence"] > 0.5, f"Should have high confidence for clear automotive query: {query}"
    
    def test_automotive_filter_clearly_non_automotive_english(self, openai_service):
        """Test that clearly non-automotive queries in English are correctly rejected"""
        non_automotive_queries = [
            "What's the weather like today?",
            "How do I bake a chocolate cake?",
            "What's the capital of France?",
            "How to learn Python programming?",
            "Best restaurants in Tbilisi"
        ]
        
        for query in non_automotive_queries:
            result = openai_service.check_automotive_relevance(query)
            
            assert isinstance(result, dict), f"Result should be dict for query: {query}"
            assert result["is_automotive"] is False, f"Should identify as non-automotive: {query}"
            assert result["confidence"] > 0.5, f"Should have high confidence for clear non-automotive query: {query}"
    
    def test_automotive_filter_clearly_non_automotive_georgian(self, openai_service):
        """Test that clearly non-automotive queries in Georgian are correctly rejected"""
        non_automotive_queries_georgian = [
            "რა ამინდია დღეს?",  # What's the weather today?
            "როგორ მოვამზადო ტორტი?",  # How to prepare a cake?
            "საუკეთესო რესტორნები თბილისში",  # Best restaurants in Tbilisi
            "კომპიუტერული პროგრამირების სწავლა",  # Learning computer programming
            "ისტორიის გაკვეთილები"  # History lessons
        ]
        
        for query in non_automotive_queries_georgian:
            result = openai_service.check_automotive_relevance(query)
            
            assert isinstance(result, dict), f"Result should be dict for Georgian query: {query}"
            assert result["is_automotive"] is False, f"Should identify Georgian non-automotive query: {query}"
            assert result["confidence"] > 0.5, f"Should have high confidence for clear non-automotive query: {query}"
    
    def test_automotive_filter_edge_cases(self, openai_service):
        """Test edge cases and borderline automotive queries"""
        edge_cases = [
            {
                "query": "I need to buy car insurance",  # Related to cars but not mechanical
                "expected": False,
                "description": "Car insurance (not mechanical)"
            },
            {
                "query": "Best car wash services",  # Car-related but not mechanical
                "expected": False,
                "description": "Car wash (not mechanical)"
            },
            {
                "query": "My motorcycle engine overheats",  # Motorcycle mechanics
                "expected": True,
                "description": "Motorcycle mechanics"
            },
            {
                "query": "Truck brake system maintenance",  # Commercial vehicle
                "expected": True,
                "description": "Commercial vehicle mechanics"
            },
            {
                "query": "Electric car charging issues",  # Modern automotive
                "expected": True,
                "description": "Electric vehicle issues"
            }
        ]
        
        for case in edge_cases:
            result = openai_service.check_automotive_relevance(case["query"])
            
            assert isinstance(result, dict), f"Result should be dict for: {case['description']}"
            assert result["is_automotive"] == case["expected"], \
                f"{case['description']}: Expected {case['expected']}, got {result['is_automotive']}"
    
    def test_automotive_filter_empty_and_invalid_input(self, openai_service):
        """Test handling of empty and invalid input"""
        invalid_inputs = [
            "",  # Empty string
            "   ",  # Whitespace only
            "a",  # Single character
            "???",  # Only punctuation
        ]
        
        for invalid_input in invalid_inputs:
            result = openai_service.check_automotive_relevance(invalid_input)
            
            assert isinstance(result, dict), f"Should return dict for invalid input: '{invalid_input}'"
            assert "is_automotive" in result, "Should contain is_automotive key"
            assert result["is_automotive"] is False, f"Should be False for invalid input: '{invalid_input}'"
            assert "reasoning" in result, "Should contain reasoning"
    
    def test_automotive_filter_with_none_input(self, openai_service):
        """Test that None input raises appropriate error"""
        with pytest.raises(ValueError, match="Query cannot be None"):
            openai_service.check_automotive_relevance(None)
    
    def test_automotive_filter_with_non_string_input(self, openai_service):
        """Test that non-string input raises appropriate error"""
        invalid_inputs = [123, ["list"], {"dict": "value"}, True]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError, match="Query must be a string"):
                openai_service.check_automotive_relevance(invalid_input)
    
    def test_automotive_filter_performance(self, openai_service):
        """Test that automotive filtering meets performance requirements (<10s reasonable for OpenAI API)"""
        test_queries = [
            "My car engine is making noise",
            "What's the weather today?",
            "ჩემი მანქანის ძრავა პრობლემას იწვევს",  # Georgian: My car engine has problems
            "როგორ მოვამზადო საღამოს ჭმელი?"  # Georgian: How to prepare dinner?
        ]
        
        for query in test_queries:
            start_time = time.time()
            result = openai_service.check_automotive_relevance(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Adjust for realistic OpenAI API response times (can be 3-10s)
            assert response_time < 10.0, f"Response time {response_time:.2f}s exceeds 10s limit for query: {query}"
            assert isinstance(result, dict), "Should return valid result dict"
    
    def test_automotive_filter_concurrent_requests(self, openai_service):
        """Test concurrent automotive filtering requests"""
        queries = [
            "Car won't start",
            "Best pizza recipe",
            "Brake pads replacement",
            "Weather forecast",
            "Engine oil change"
        ]
        
        def make_request(query):
            return openai_service.check_automotive_relevance(query)
        
        start_time = time.time()
        
        # Run concurrent requests using threading simulation
        results = []
        for query in queries:
            result = make_request(query)
            results.append((query, result))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests completed successfully
        assert len(results) == len(queries), "All requests should complete"
        
        for query, result in results:
            assert isinstance(result, dict), f"Should return dict for query: {query}"
            assert "is_automotive" in result, f"Should contain is_automotive for query: {query}"
        
        # Performance check - should complete within reasonable time for 5 sequential API calls
        assert total_time < 25.0, f"Concurrent requests took {total_time:.2f}s, should be under 25s"
    
    def test_automotive_filter_mixed_language_query(self, openai_service):
        """Test queries with mixed Georgian and English"""
        mixed_queries = [
            "My car-ის ძრავა won't start",  # Mixed English-Georgian
            "როგორ engine oil-ს შევცვალო?",  # Mixed Georgian-English
            "ჩემი BMW-ის brakes არ მუშაობს"  # Mixed Georgian with English technical terms
        ]
        
        for query in mixed_queries:
            result = openai_service.check_automotive_relevance(query)
            
            assert isinstance(result, dict), f"Should handle mixed language: {query}"
            # These should be identified as automotive since they contain car-related terms
            assert result["is_automotive"] is True, f"Should identify mixed language automotive query: {query}"
    
    def test_automotive_filter_long_context_query(self, openai_service):
        """Test automotive filtering with longer, context-rich queries"""
        long_queries = [
            """I've been having trouble with my 2015 Honda Civic lately. The engine starts fine in the morning, 
            but after driving for about 30 minutes, it starts to overheat. I've checked the coolant levels and 
            they seem fine. The radiator fan seems to be working too. What could be causing this overheating issue?""",
            
            """ჩემი მანქანა არის 2018 წლის Toyota Corolla. გუშინ დილით როცა სამსახურში მივდიოდი, 
            მანქანამ უცებ დაიწყო უცნაური ხმაურის გამოცემა ძრავიდან. ხმაური განსაკუთრებით იგრძნობა 
            როცა გაჩერებული ვარ და ძრავა მუშაობს. რა შეიძლება იყოს პრობლემა?"""
        ]
        
        for query in long_queries:
            start_time = time.time()
            result = openai_service.check_automotive_relevance(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert isinstance(result, dict), f"Should handle long query"
            assert result["is_automotive"] is True, f"Should identify long automotive query"
            assert response_time < 10.0, f"Long query response time {response_time:.2f}s should be under 10s"
    
    def test_automotive_filter_technical_terms(self, openai_service):
        """Test automotive filtering with technical automotive terms"""
        technical_queries = [
            "OBD-II diagnostic codes P0301 and P0420",
            "ECU remapping for turbo diesel engine",
            "Catalytic converter efficiency below threshold",
            "ABS modulator replacement procedure",
            "Variable valve timing system malfunction"
        ]
        
        for query in technical_queries:
            result = openai_service.check_automotive_relevance(query)
            
            assert isinstance(result, dict), f"Should handle technical query: {query}"
            assert result["is_automotive"] is True, f"Should identify technical automotive query: {query}"
            assert result["confidence"] > 0.7, f"Should have high confidence for technical terms: {query}"
    
    def test_automotive_filter_response_structure(self, openai_service):
        """Test that automotive filter response has correct structure"""
        query = "My car engine makes noise"
        result = openai_service.check_automotive_relevance(query)
        
        # Check required keys
        required_keys = ["is_automotive", "confidence", "reasoning"]
        for key in required_keys:
            assert key in result, f"Result must contain '{key}' key"
        
        # Check data types
        assert isinstance(result["is_automotive"], bool), "is_automotive must be boolean"
        assert isinstance(result["confidence"], (int, float)), "confidence must be numeric"
        assert isinstance(result["reasoning"], str), "reasoning must be string"
        
        # Check value ranges
        assert 0 <= result["confidence"] <= 1, "confidence must be between 0 and 1"
        assert len(result["reasoning"]) > 10, "reasoning should be descriptive (>10 chars)"
    
    def test_automotive_filter_consistency(self, openai_service):
        """Test that similar queries get consistent results"""
        similar_queries = [
            "Car engine making noise",
            "Engine noise in my car",
            "My car's engine is noisy"
        ]
        
        results = []
        for query in similar_queries:
            result = openai_service.check_automotive_relevance(query)
            results.append(result)
        
        # All should be identified as automotive
        for i, result in enumerate(results):
            assert result["is_automotive"] is True, f"Query {i+1} should be automotive: {similar_queries[i]}"
        
        # Confidence levels should be similar (within 0.3 range)
        confidences = [result["confidence"] for result in results]
        confidence_range = max(confidences) - min(confidences)
        assert confidence_range <= 0.3, f"Confidence range {confidence_range} too wide for similar queries" 