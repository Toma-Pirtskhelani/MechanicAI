import pytest
import time
from app.services.openai_service import OpenAIService


class TestTranslationService:
    """Test translation service functionality with real OpenAI API integration"""
    
    @pytest.fixture
    def openai_service(self):
        """Create OpenAI service instance for testing"""
        return OpenAIService()
    
    def test_detect_language_english(self, openai_service):
        """Test language detection for English text"""
        english_queries = [
            "My car engine is making a strange noise",
            "How often should I change the oil?",
            "The brake pedal feels soft",
            "Check engine light is on",
            "Need help with transmission problems"
        ]
        
        for query in english_queries:
            result = openai_service.detect_language(query)
            assert result["language"] == "en"
            assert 0.7 <= result["confidence"] <= 1.0
            assert "reasoning" in result
    
    def test_detect_language_georgian(self, openai_service):
        """Test language detection for Georgian text"""
        georgian_queries = [
            "ჩემი მანქანის ძრავა უცნაური ხმაუროვნებს აკეთებს",
            "რამდენად ხშირად უნდა შევცვალო ზეთი?",
            "სამუხრუჭე პედალი რბილი ყოფილა",
            "ძრავის ინდიკატორი ანთია",
            "მჭირდება დახმარება გადაცემათა კოლოფის პრობლემებთან"
        ]
        
        for query in georgian_queries:
            result = openai_service.detect_language(query)
            assert result["language"] == "ka"
            assert 0.7 <= result["confidence"] <= 1.0
            assert "reasoning" in result
    
    def test_detect_language_mixed(self, openai_service):
        """Test language detection for mixed Georgian-English text"""
        mixed_queries = [
            "My მანქანა has engine problems",
            "ძრავის oil change როდის უნდა?",
            "brake პედალი არ მუშაობს",
            "Check ძრავის light ანთია",
            "transmission გადაცემათა კოლოფი problems"
        ]
        
        for query in mixed_queries:
            result = openai_service.detect_language(query)
            assert result["language"] in ["mixed", "en", "ka"]  # Any of these is acceptable
            assert 0.5 <= result["confidence"] <= 1.0
            assert "reasoning" in result
    
    def test_detect_language_edge_cases(self, openai_service):
        """Test language detection edge cases"""
        # Empty string
        result = openai_service.detect_language("")
        assert result["language"] == "en"  # Default to English
        assert "reasoning" in result
        
        # Numbers and symbols only
        result = openai_service.detect_language("123 !@# $%^")
        assert result["language"] == "en"  # Default to English
        assert "reasoning" in result
        
        # Very short text
        result = openai_service.detect_language("P0301")
        assert result["language"] in ["en", "mixed"]
        assert "reasoning" in result
    
    def test_translate_to_georgian_simple(self, openai_service):
        """Test English to Georgian translation for simple automotive text"""
        english_texts = [
            "Check your engine oil level",
            "Your brake pads need replacement",
            "The battery is dead",
            "Engine overheating",
            "Change transmission fluid"
        ]
        
        for text in english_texts:
            start_time = time.time()
            result = openai_service.translate_to_georgian(text)
            end_time = time.time()
            
            # Performance check
            assert (end_time - start_time) < 10, "Translation should complete within 10 seconds"
            
            # Validate response structure
            assert "translated_text" in result
            assert "confidence" in result
            assert "original_language" in result
            
            # Check translation quality
            assert len(result["translated_text"]) > 0
            assert result["confidence"] >= 0.6
            assert result["original_language"] == "en"
            
            # Check for Georgian characters in translation
            translated = result["translated_text"]
            georgian_chars = sum(1 for char in translated if '\u10A0' <= char <= '\u10FF')
            assert georgian_chars > 0, f"Translation should contain Georgian characters: {translated}"
    
    def test_translate_to_english_simple(self, openai_service):
        """Test Georgian to English translation for simple automotive text"""
        georgian_texts = [
            "შეამოწმეთ ძრავის ზეთის დონე",
            "თქვენი სამუხრუჭე ბალიშები ჩასანაცვლებელია",
            "ბატარეა გამწვავებულია",
            "ძრავის გადახურება",
            "შეცვალეთ გადაცემათა სითხე"
        ]
        
        for text in georgian_texts:
            start_time = time.time()
            result = openai_service.translate_to_english(text)
            end_time = time.time()
            
            # Performance check
            assert (end_time - start_time) < 10, "Translation should complete within 10 seconds"
            
            # Validate response structure
            assert "translated_text" in result
            assert "confidence" in result
            assert "original_language" in result
            
            # Check translation quality
            assert len(result["translated_text"]) > 0
            assert result["confidence"] >= 0.6
            assert result["original_language"] == "ka"
            
            # Check for English text in translation
            translated = result["translated_text"]
            english_chars = sum(1 for char in translated if char.isalpha() and char.isascii())
            assert english_chars > len(translated) * 0.7, f"Translation should be primarily English: {translated}"
    
    def test_translate_technical_automotive_terms(self, openai_service):
        """Test translation of technical automotive terms"""
        # English technical terms to Georgian
        technical_en = [
            "OBD-II diagnostic trouble code P0301",
            "Catalytic converter efficiency below threshold",
            "Anti-lock Braking System malfunction",
            "Engine Control Unit diagnostic report",
            "Transmission Control Module failure"
        ]
        
        for term in technical_en:
            result = openai_service.translate_to_georgian(term)
            assert result["confidence"] >= 0.5  # Technical terms may be harder
            assert len(result["translated_text"]) > 0
            
        # Georgian technical terms to English
        technical_ka = [
            "ძრავის მართვის ბლოკის დიაგნოსტიკა",
            "სამუხრუჭე სისტემის გაუმართაობა",
            "გადაცემათა კოლოფის კონტროლერი",
            "კატალიზატორის ეფექტურობა",
            "ანტიბლოკირების სისტემა"
        ]
        
        for term in technical_ka:
            result = openai_service.translate_to_english(term)
            assert result["confidence"] >= 0.5  # Technical terms may be harder
            assert len(result["translated_text"]) > 0
    
    def test_auto_translate_response_english_user(self, openai_service):
        """Test automatic response translation when user writes in English"""
        english_query = "My car engine is overheating, what should I do?"
        georgian_response = "დაუყოვნებლივ გააჩერეთ მანქანა და ყიდეთ ძრავა. შეამოწმეთ გამაგრილებელი სითხის დონე."
        
        result = openai_service.auto_translate_response(
            user_query=english_query,
            system_response=georgian_response
        )
        
        # Should translate Georgian response to English
        assert result["needs_translation"] == True
        assert result["user_language"] == "en"
        assert result["response_language"] == "ka"
        assert "translated_response" in result
        assert result["confidence"] >= 0.6
        
        # Check translation quality
        translated = result["translated_response"]
        english_chars = sum(1 for char in translated if char.isalpha() and char.isascii())
        assert english_chars > len(translated) * 0.7, "Response should be translated to English"
    
    def test_auto_translate_response_georgian_user(self, openai_service):
        """Test automatic response translation when user writes in Georgian"""
        georgian_query = "ჩემი მანქანის ძრავა ზედმეტად ცხელდება, რა ვქნა?"
        english_response = "Immediately stop the car and turn off the engine. Check the coolant level."
        
        result = openai_service.auto_translate_response(
            user_query=georgian_query,
            system_response=english_response
        )
        
        # Should translate English response to Georgian
        assert result["needs_translation"] == True
        assert result["user_language"] == "ka"
        assert result["response_language"] == "en"
        assert "translated_response" in result
        assert result["confidence"] >= 0.6
        
        # Check translation quality
        translated = result["translated_response"]
        georgian_chars = sum(1 for char in translated if '\u10A0' <= char <= '\u10FF')
        assert georgian_chars > 0, "Response should be translated to Georgian"
    
    def test_auto_translate_response_same_language(self, openai_service):
        """Test auto translation when query and response are in same language"""
        english_query = "What causes engine knock?"
        english_response = "Engine knock is typically caused by improper fuel octane or carbon buildup."
        
        result = openai_service.auto_translate_response(
            user_query=english_query,
            system_response=english_response
        )
        
        # Should not need translation
        assert result["needs_translation"] == False
        assert result["user_language"] == "en"
        assert result["response_language"] == "en"
        assert result["translated_response"] == english_response
        assert result["confidence"] >= 0.8
    
    def test_translation_preserves_technical_codes(self, openai_service):
        """Test that translation preserves technical codes and numbers"""
        text_with_codes = "Diagnostic code P0301 indicates cylinder 1 misfire. Check spark plug gap: 0.8mm."
        
        result = openai_service.translate_to_georgian(text_with_codes)
        translated = result["translated_text"]
        
        # Technical codes should be preserved
        assert "P0301" in translated
        # Accept various formats for measurements
        assert ("0.8mm" in translated or "0.8 მმ" in translated or "0.8მმ" in translated)
        assert "1" in translated
    
    def test_translation_error_handling(self, openai_service):
        """Test translation error handling"""
        # Test with None input
        with pytest.raises(ValueError, match="Text cannot be None"):
            openai_service.translate_to_georgian(None)
        
        with pytest.raises(ValueError, match="Text cannot be None"):
            openai_service.translate_to_english(None)
        
        # Test with non-string input
        with pytest.raises(ValueError, match="Text must be a string"):
            openai_service.translate_to_georgian(123)
        
        with pytest.raises(ValueError, match="Text must be a string"):
            openai_service.translate_to_english(["text"])
    
    def test_translation_performance_requirements(self, openai_service):
        """Test translation performance requirements"""
        long_text = """
        The engine control unit (ECU) is reporting multiple diagnostic trouble codes. 
        The primary codes are P0301, P0302, P0303, and P0304, which indicate misfires 
        in cylinders 1, 2, 3, and 4 respectively. This suggests a systemic issue rather 
        than individual cylinder problems. Check the ignition coil pack, spark plug wires, 
        fuel injectors, and compression. The vacuum system should also be inspected for leaks.
        """
        
        start_time = time.time()
        result = openai_service.translate_to_georgian(long_text)
        end_time = time.time()
        
        # Performance requirement: <10 seconds
        assert (end_time - start_time) < 10, "Long text translation should complete within 10 seconds"
        assert result["confidence"] >= 0.5
        assert len(result["translated_text"]) > 100  # Should be substantial translation
    
    def test_batch_translation_consistency(self, openai_service):
        """Test translation consistency across multiple calls"""
        test_phrase = "Check engine oil level"
        
        # Translate same phrase multiple times
        results = []
        for _ in range(3):
            result = openai_service.translate_to_georgian(test_phrase)
            results.append(result["translated_text"])
        
        # Results should be reasonably consistent (allowing some variation)
        # At least the key automotive terms should be translated similarly
        for i, result in enumerate(results):
            assert len(result) > 0
            assert "ძრავი" in result or "ზეთი" in result  # Should contain key Georgian terms 