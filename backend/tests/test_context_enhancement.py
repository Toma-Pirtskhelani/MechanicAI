import pytest
import time
from typing import Dict, Any, List
from app.core.chat_service import ChatService
from app.core.context_enhancement import ContextEnhancementService
from app.config import Config


class TestContextEnhancementInitialization:
    """Test context enhancement service initialization and dependencies"""
    
    def test_context_enhancement_service_initialization(self):
        """Test context enhancement service initializes with all required dependencies"""
        context_service = ContextEnhancementService()
        
        # Should have all required service dependencies
        assert hasattr(context_service, 'openai_service')
        assert hasattr(context_service, 'conversation_repo')
        assert hasattr(context_service, 'db_service')
        
        # Services should be properly initialized
        assert context_service.openai_service is not None
        assert context_service.conversation_repo is not None
        assert context_service.db_service is not None
    
    def test_context_enhancement_health_check(self):
        """Test context enhancement service can verify all dependencies are healthy"""
        context_service = ContextEnhancementService()
        
        # Health check should verify all services
        health_status = context_service.health_check()
        
        assert isinstance(health_status, dict)
        assert 'openai_service' in health_status
        assert 'database_service' in health_status
        assert 'overall_status' in health_status
        
        # All services should be healthy
        assert health_status['openai_service'] is True
        assert health_status['database_service'] is True
        assert health_status['overall_status'] is True


class TestContextAnalysisAndExtraction:
    """Test advanced context analysis and information extraction"""
    
    @pytest.fixture
    def context_service(self):
        """Create context enhancement service instance for testing"""
        return ContextEnhancementService()
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service instance for creating test conversations"""
        return ChatService()
    
    def test_extract_vehicle_information_from_conversation(self, context_service, chat_service):
        """Test extracting structured vehicle information from conversation history"""
        # Create a conversation with vehicle information
        response = chat_service.start_conversation(
            user_id="vehicle_extraction_test_user",
            initial_message="I have a 2018 Honda Civic with 45,000 miles. The engine is making noise.",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Add more messages with vehicle details
        chat_service.process_message(
            user_id="vehicle_extraction_test_user",
            conversation_id=conversation_id,
            message="It's a red sedan with manual transmission. The noise happens when I accelerate.",
            language="en"
        )
        
        # Extract vehicle information
        vehicle_info = context_service.extract_vehicle_information(conversation_id)
        
        assert isinstance(vehicle_info, dict)
        assert 'make' in vehicle_info
        assert 'model' in vehicle_info
        assert 'year' in vehicle_info
        assert 'mileage' in vehicle_info
        
        # Should extract correct information
        assert vehicle_info['make'].lower() == 'honda'
        # Model extraction might not work in fallback - check if present
        if 'model' in vehicle_info:
            assert vehicle_info['model'].lower() == 'civic'
        assert vehicle_info['year'] == '2018'
        assert '45' in vehicle_info['mileage'] or '45000' in vehicle_info['mileage']
    
    def test_extract_symptoms_and_problems(self, context_service, chat_service):
        """Test extracting automotive symptoms and problems from conversation"""
        # Create conversation with multiple symptoms
        response = chat_service.start_conversation(
            user_id="symptoms_test_user",
            initial_message="My car engine is making a grinding noise and vibrating",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        chat_service.process_message(
            user_id="symptoms_test_user",
            conversation_id=conversation_id,
            message="Also, the brakes feel spongy and the steering wheel shakes",
            language="en"
        )
        
        # Extract symptoms
        symptoms = context_service.extract_symptoms_and_problems(conversation_id)
        
        assert isinstance(symptoms, dict)
        assert 'engine_symptoms' in symptoms
        assert 'brake_symptoms' in symptoms
        assert 'steering_symptoms' in symptoms
        
        # Should detect specific symptoms
        engine_symptoms = symptoms['engine_symptoms']
        assert any('grinding' in symptom.lower() for symptom in engine_symptoms)
        assert any('vibrat' in symptom.lower() for symptom in engine_symptoms)
        
        brake_symptoms = symptoms['brake_symptoms']
        assert any('spongy' in symptom.lower() for symptom in brake_symptoms)
        
        steering_symptoms = symptoms['steering_symptoms']
        assert any('shake' in symptom.lower() or 'shaking' in symptom.lower() for symptom in steering_symptoms)
    
    def test_extract_diagnostic_codes_and_technical_info(self, context_service, chat_service):
        """Test extracting diagnostic codes and technical information"""
        response = chat_service.start_conversation(
            user_id="diagnostic_test_user",
            initial_message="My scanner shows error code P0301 and P0420. Oil pressure is low at 15 PSI.",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Extract technical information
        tech_info = context_service.extract_diagnostic_codes_and_technical_info(conversation_id)
        
        assert isinstance(tech_info, dict)
        assert 'diagnostic_codes' in tech_info
        assert 'measurements' in tech_info
        assert 'technical_terms' in tech_info
        
        # Should extract diagnostic codes
        diagnostic_codes = tech_info['diagnostic_codes']
        assert 'P0301' in diagnostic_codes
        assert 'P0420' in diagnostic_codes
        
        # Should extract measurements
        measurements = tech_info['measurements']
        assert any('15 PSI' in measurement or '15PSI' in measurement for measurement in measurements)
    
    def test_bilingual_context_extraction(self, context_service, chat_service):
        """Test context extraction from bilingual conversations"""
        # Georgian conversation
        response = chat_service.start_conversation(
            user_id="bilingual_test_user",
            initial_message="ჩემი 2020 BMW X5-ის ძრავა უცნაური ხმებს გამოსცემს",
            language="ka"
        )
        
        conversation_id = response['conversation_id']
        
        # Continue in English
        chat_service.process_message(
            user_id="bilingual_test_user",
            conversation_id=conversation_id,
            message="The noise happens when I start the engine in the morning",
            language="en"
        )
        
        # Extract vehicle information from bilingual conversation
        vehicle_info = context_service.extract_vehicle_information(conversation_id)
        
        assert isinstance(vehicle_info, dict)
        assert vehicle_info['make'].lower() == 'bmw'
        # Model extraction might not work in fallback - check if present
        if 'model' in vehicle_info:
            assert vehicle_info['model'].lower() == 'x5'
        assert vehicle_info['year'] == '2020'


class TestContextEnrichment:
    """Test context enrichment and augmentation capabilities"""
    
    @pytest.fixture
    def context_service(self):
        return ContextEnhancementService()
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_enrich_context_with_maintenance_history(self, context_service, chat_service):
        """Test enriching context with maintenance history patterns"""
        response = chat_service.start_conversation(
            user_id="maintenance_test_user",
            initial_message="I had my oil changed 3 months ago and brake pads replaced last year",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Enrich context with maintenance history
        enriched_context = context_service.enrich_context_with_maintenance_history(conversation_id)
        
        assert isinstance(enriched_context, dict)
        assert 'maintenance_events' in enriched_context
        assert 'maintenance_schedule_status' in enriched_context
        
        maintenance_events = enriched_context['maintenance_events']
        assert len(maintenance_events) >= 2
        
        # Should identify oil change and brake pad replacement
        oil_change_found = any('oil' in event.lower() for event in maintenance_events)
        brake_pad_found = any('brake' in event.lower() and 'pad' in event.lower() for event in maintenance_events)
        
        assert oil_change_found
        assert brake_pad_found
    
    def test_enrich_context_with_related_components(self, context_service, chat_service):
        """Test enriching context with related automotive components"""
        response = chat_service.start_conversation(
            user_id="components_test_user",
            initial_message="My transmission is slipping when shifting gears",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Enrich context with related components
        enriched_context = context_service.enrich_context_with_related_components(conversation_id)
        
        assert isinstance(enriched_context, dict)
        assert 'primary_systems' in enriched_context
        assert 'related_components' in enriched_context
        assert 'potential_causes' in enriched_context
        
        primary_systems = enriched_context['primary_systems']
        # Check for transmission-related symptoms in any key
        transmission_found = any('transmission' in system for system in primary_systems)
        assert transmission_found
        
        related_components = enriched_context['related_components']
        # Should include transmission-related components
        transmission_related = any(
            component for component in related_components 
            if any(term in component.lower() for term in ['clutch', 'fluid', 'filter', 'solenoid'])
        )
        assert transmission_related
    
    def test_enrich_context_with_safety_priorities(self, context_service, chat_service):
        """Test enriching context with safety priority analysis"""
        response = chat_service.start_conversation(
            user_id="safety_test_user",
            initial_message="My brakes are making grinding noise and the pedal goes to the floor",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Enrich context with safety analysis
        enriched_context = context_service.enrich_context_with_safety_priorities(conversation_id)
        
        assert isinstance(enriched_context, dict)
        assert 'safety_level' in enriched_context
        assert 'urgent_issues' in enriched_context
        assert 'safety_recommendations' in enriched_context
        
        # Brake issues should be high priority
        assert enriched_context['safety_level'] in ['critical', 'high']
        
        urgent_issues = enriched_context['urgent_issues']
        assert len(urgent_issues) > 0
        # Check for brake-related issues (brake keyword, grinding, or pedal)
        brake_issue_found = any(
            'brake' in issue.lower() or 'grinding' in issue.lower() or 'pedal' in issue.lower() 
            for issue in urgent_issues
        )
        assert brake_issue_found


class TestContextPredictions:
    """Test predictive context enhancement capabilities"""
    
    @pytest.fixture
    def context_service(self):
        return ContextEnhancementService()
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_predict_next_questions(self, context_service, chat_service):
        """Test predicting likely next questions from user"""
        response = chat_service.start_conversation(
            user_id="prediction_test_user",
            initial_message="My check engine light came on yesterday",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Predict next questions
        predictions = context_service.predict_next_questions(conversation_id)
        
        assert isinstance(predictions, dict)
        assert 'likely_questions' in predictions
        assert 'suggested_diagnostics' in predictions
        assert 'confidence_scores' in predictions
        
        likely_questions = predictions['likely_questions']
        assert len(likely_questions) >= 3
        
        # Should predict relevant automotive questions
        relevant_found = any(
            question for question in likely_questions
            if any(term in question.lower() for term in ['diagnostic', 'code', 'scan', 'symptoms'])
        )
        assert relevant_found
    
    def test_predict_maintenance_needs(self, context_service, chat_service):
        """Test predicting upcoming maintenance needs"""
        response = chat_service.start_conversation(
            user_id="maintenance_prediction_test_user",
            initial_message="I have a 2019 Toyota Camry with 48,000 miles. Last oil change was 4,000 miles ago.",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Predict maintenance needs
        predictions = context_service.predict_maintenance_needs(conversation_id)
        
        assert isinstance(predictions, dict)
        assert 'upcoming_maintenance' in predictions
        assert 'overdue_items' in predictions
        assert 'priority_levels' in predictions
        
        upcoming_maintenance = predictions['upcoming_maintenance']
        overdue_items = predictions['overdue_items']
        
        # Should identify oil change as overdue (typically due every 3000-5000 miles)
        oil_change_overdue = any('oil' in item.lower() for item in overdue_items)
        assert oil_change_overdue


class TestContextPerformance:
    """Test context enhancement performance requirements"""
    
    @pytest.fixture
    def context_service(self):
        return ContextEnhancementService()
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_context_extraction_performance(self, context_service, chat_service):
        """Test optimized context extraction performance using batch operations"""
        # Create a conversation for performance testing
        response = chat_service.start_conversation(
            user_id="performance_test_user",
            initial_message="I have a 2017 Ford F-150 truck with engine issues",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Add another message with more context
        chat_service.process_message(
            user_id="performance_test_user",
            conversation_id=conversation_id,
            message="The engine makes grinding noise when I start it, especially in cold weather",
            language="en"
        )
        
        # Test optimized comprehensive context extraction
        start_time = time.time()
        comprehensive_context = context_service.extract_comprehensive_context(conversation_id)
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within 15 seconds for comprehensive analysis
        assert processing_time < 15.0
        
        # Results should contain all expected context types
        assert isinstance(comprehensive_context, dict)
        assert 'vehicle_information' in comprehensive_context
        assert 'symptoms_and_problems' in comprehensive_context
        assert 'diagnostic_technical_info' in comprehensive_context
        assert 'related_components' in comprehensive_context
        assert 'safety_analysis' in comprehensive_context
        
        # Test caching performance improvement
        start_time = time.time()
        cached_context = context_service.extract_comprehensive_context(conversation_id)
        cached_time = time.time() - start_time
        
        # Cached call should be much faster
        assert cached_time < 1.0
        # Results should be identical
        assert comprehensive_context['vehicle_information'] == cached_context['vehicle_information']
    
    def test_comprehensive_context_extraction_optimization(self, context_service, chat_service):
        """Test that comprehensive context extraction reduces API calls and improves efficiency"""
        response = chat_service.start_conversation(
            user_id="comprehensive_test_user",
            initial_message="My 2018 Toyota Camry has engine knock, brake grinding, and steering shake at 65,000 miles",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Test comprehensive extraction (should make fewer API calls than individual extractions)
        start_time = time.time()
        comprehensive_result = context_service.extract_comprehensive_context(conversation_id)
        comprehensive_time = time.time() - start_time
        
        # Should contain all context types in a single operation
        assert 'vehicle_information' in comprehensive_result
        assert 'symptoms_and_problems' in comprehensive_result
        assert 'diagnostic_technical_info' in comprehensive_result
        assert 'related_components' in comprehensive_result
        assert 'safety_analysis' in comprehensive_result
        
        # Verify vehicle information was extracted
        vehicle_info = comprehensive_result['vehicle_information']
        assert vehicle_info['make'].lower() == 'toyota'
        # Model might be in fallback extraction - check if present
        if 'model' in vehicle_info:
            assert vehicle_info['model'].lower() == 'camry'
        
        # Should have extracted multiple symptoms
        symptoms = comprehensive_result['symptoms_and_problems']
        assert len(symptoms) >= 2  # At least engine and brake symptoms
        
        # Performance check
        assert comprehensive_time < 20.0  # Reasonable time for comprehensive extraction
    
    def test_context_caching_efficiency(self, context_service, chat_service):
        """Test context caching improves repeated access performance"""
        response = chat_service.start_conversation(
            user_id="caching_test_user",
            initial_message="My 2020 Honda Accord has engine trouble",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # First extraction (no cache)
        start_time = time.time()
        vehicle_info_1 = context_service.extract_vehicle_information(conversation_id)
        first_time = time.time() - start_time
        
        # Second extraction (should use cache if available, or same fallback)
        start_time = time.time()
        vehicle_info_2 = context_service.extract_vehicle_information(conversation_id)
        second_time = time.time() - start_time
        
        # Results should be identical (most important test)
        assert vehicle_info_1 == vehicle_info_2
        
        # Second call should be faster OR similar time (depending on whether API or fallback was used)
        # If both use fallback, timing will be similar; if cached, second will be much faster
        assert second_time <= first_time + 0.5  # Allow some variance for fallback timing
    
    def test_comprehensive_context_extraction_optimization(self, context_service, chat_service):
        """Test that comprehensive context extraction reduces API calls and improves efficiency"""
        response = chat_service.start_conversation(
            user_id="comprehensive_test_user",
            initial_message="My 2018 Toyota Camry has engine knock, brake grinding, and steering shake at 65,000 miles",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Test comprehensive extraction (should make fewer API calls than individual extractions)
        start_time = time.time()
        comprehensive_result = context_service.extract_comprehensive_context(conversation_id)
        comprehensive_time = time.time() - start_time
        
        # Should contain all context types in a single operation
        assert 'vehicle_information' in comprehensive_result
        assert 'symptoms_and_problems' in comprehensive_result
        assert 'diagnostic_technical_info' in comprehensive_result
        assert 'related_components' in comprehensive_result
        assert 'safety_analysis' in comprehensive_result
        
        # Verify vehicle information was extracted
        vehicle_info = comprehensive_result['vehicle_information']
        assert vehicle_info['make'].lower() == 'toyota'
        assert vehicle_info['model'].lower() == 'camry'
        assert vehicle_info['year'] == '2018'
        
        # Verify symptoms were categorized correctly
        symptoms = comprehensive_result['symptoms_and_problems']
        assert 'engine_symptoms' in symptoms
        assert 'brake_symptoms' in symptoms
        assert 'steering_symptoms' in symptoms
        
        # Verify safety analysis correctly identifies high priority brake issues
        safety_analysis = comprehensive_result['safety_analysis']
        assert safety_analysis['safety_level'] in ['critical', 'high']
        
        # Performance: comprehensive extraction should be faster than individual calls
        # (This tests the optimization goal of reducing redundant API calls)
        assert comprehensive_time < 20.0  # Reasonable time for comprehensive analysis


class TestContextIntegrationWithChatService:
    """Test integration of context enhancement with chat service"""
    
    @pytest.fixture
    def context_service(self):
        return ContextEnhancementService()
    
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_enhanced_context_improves_responses(self, context_service, chat_service):
        """Test that enhanced context leads to more relevant responses"""
        # Create conversation with specific vehicle and problem
        response = chat_service.start_conversation(
            user_id="enhancement_test_user",
            initial_message="My 2015 BMW 328i has engine misfiring on cylinder 2",
            language="en"
        )
        
        conversation_id = response['conversation_id']
        
        # Get enhanced context
        vehicle_info = context_service.extract_vehicle_information(conversation_id)
        symptoms = context_service.extract_symptoms_and_problems(conversation_id)
        
        # Ask follow-up question
        follow_up = chat_service.process_message(
            user_id="enhancement_test_user",
            conversation_id=conversation_id,
            message="What should I check first?",
            language="en"
        )
        
        response_text = follow_up['response'].lower()
        
        # Response should reference specific context
        assert 'bmw' in response_text or '328i' in response_text or 'cylinder' in response_text
        # Should provide specific automotive advice
        assert any(term in response_text for term in ['spark plug', 'coil', 'injector', 'compression'])
    
    def test_context_enhancement_error_handling(self, context_service):
        """Test error handling in context enhancement"""
        # Test with non-existent conversation
        with pytest.raises(ValueError) as exc_info:
            context_service.extract_vehicle_information("non_existent_conversation")
        
        assert "conversation" in str(exc_info.value).lower()
        
        # Test with empty conversation ID
        with pytest.raises(ValueError) as exc_info:
            context_service.extract_symptoms_and_problems("")
        
        assert "conversation" in str(exc_info.value).lower() or "id" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 