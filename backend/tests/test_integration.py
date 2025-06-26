import pytest
from app.config import Config
from app.db.database_service import DatabaseService
from openai import OpenAI
from supabase import create_client


class TestSystemIntegration:
    """Integration tests for the complete system setup"""
    
    def test_complete_initialization_flow(self):
        """Test the complete system initialization from config to database"""
        # Step 1: Configuration should load correctly
        config_validation = Config.validate_required_env_vars()
        assert config_validation["status"] == "ok", f"Configuration failed: {config_validation}"
        
        # Step 2: Database should connect successfully
        db = DatabaseService()
        health = db.health_check()
        assert health["status"] == "healthy", f"Database unhealthy: {health}"
        
        # Step 3: All required tables should exist
        required_tables = ["conversations", "messages", "conversation_contexts"]
        tables = db.get_tables()
        for table in required_tables:
            assert table in tables, f"Required table '{table}' missing"
        
        # Step 4: Database operations should work
        crud_result = db.test_crud_operations()
        assert crud_result["error"] is None, f"CRUD operations failed: {crud_result['error']}"
        
        # Step 5: OpenAI connection should work
        openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        models = openai_client.models.list()
        assert len(models.data) > 0, "OpenAI API not accessible"
        
        # Step 6: Supabase connection should work independently
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        test_result = supabase_client.table('conversations').select("count", count="exact").limit(0).execute()
        assert hasattr(test_result, 'count'), "Supabase API not accessible"
    
    def test_end_to_end_conversation_workflow(self):
        """Test a complete conversation workflow from start to finish"""
        db = DatabaseService()
        
        # Step 1: Create a conversation (simulating new user interaction)
        conversation_data = {
            "user_id": "integration_test_user_001",
            "language": "en",
            "status": "active",
            "title": "Car Engine Problem"
        }
        
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        try:
            # Step 2: Add user message
            user_message = {
                "conversation_id": conversation_id,
                "role": "user",
                "content": "My car engine is making a weird noise when I start it. What could be wrong?",
                "language": "en",
                "is_automotive": True
            }
            
            user_msg_result = db.client.table('messages').insert(user_message).execute()
            user_message_id = user_msg_result.data[0]['id']
            
            # Step 3: Add assistant response
            assistant_message = {
                "conversation_id": conversation_id,
                "role": "assistant", 
                "content": "Based on your description, the weird noise when starting could be several things: 1) Low oil level causing engine knock, 2) Starter motor issues, 3) Belt problems. I recommend checking your oil level first.",
                "language": "en",
                "is_automotive": True
            }
            
            assistant_msg_result = db.client.table('messages').insert(assistant_message).execute()
            assistant_message_id = assistant_msg_result.data[0]['id']
            
            # Step 4: Create conversation context (simulating context compression)
            context_data = {
                "conversation_id": conversation_id,
                "compressed_context": '{"summary": "User reports engine noise on startup", "key_points": ["engine noise", "startup issue"], "recommendations": ["check oil level", "inspect starter", "examine belts"]}',
                "message_count": 2,
                "is_active": True
            }
            
            context_result = db.client.table('conversation_contexts').insert(context_data).execute()
            context_id = context_result.data[0]['id']
            
            # Step 5: Verify complete conversation state
            # Get conversation with all messages
            messages = db.client.table('messages').select("*").eq('conversation_id', conversation_id).order('created_at').execute()
            assert len(messages.data) == 2
            assert messages.data[0]['role'] == 'user'
            assert messages.data[1]['role'] == 'assistant'
            assert messages.data[0]['is_automotive'] is True
            assert messages.data[1]['is_automotive'] is True
            
            # Get conversation context
            contexts = db.client.table('conversation_contexts').select("*").eq('conversation_id', conversation_id).execute()
            assert len(contexts.data) == 1
            assert contexts.data[0]['message_count'] == 2
            assert contexts.data[0]['is_active'] is True
            
            # Step 6: Verify conversation is retrievable
            conversation = db.client.table('conversations').select("*").eq('id', conversation_id).execute()
            assert len(conversation.data) == 1
            assert conversation.data[0]['status'] == 'active'
            assert conversation.data[0]['language'] == 'en'
            
            # Step 7: Test conversation closure
            db.client.table('conversations').update({"status": "closed"}).eq('id', conversation_id).execute()
            
            closed_conversation = db.client.table('conversations').select("*").eq('id', conversation_id).execute()
            assert closed_conversation.data[0]['status'] == 'closed'
            
        finally:
            # Cleanup: Delete conversation (should cascade to messages and contexts)
            db.client.table('conversations').delete().eq('id', conversation_id).execute()
    
    def test_bilingual_conversation_workflow(self):
        """Test bilingual conversation handling (Georgian and English)"""
        db = DatabaseService()
        
        # Test Georgian conversation
        georgian_conversation = {
            "user_id": "bilingual_test_user",
            "language": "ka",
            "status": "active",
            "title": "ავტომობილის პრობლემა"
        }
        
        ka_conv_result = db.client.table('conversations').insert(georgian_conversation).execute()
        ka_conversation_id = ka_conv_result.data[0]['id']
        
        try:
            # Georgian user message
            ka_user_message = {
                "conversation_id": ka_conversation_id,
                "role": "user",
                "content": "ჩემს მანქანას ძრავა უცნაური ხმაურს გამოსცემს. რა შეიძლება იყოს პრობლემა?",
                "language": "ka",
                "is_automotive": True
            }
            
            ka_user_result = db.client.table('messages').insert(ka_user_message).execute()
            
            # English response (simulating translation)
            ka_assistant_message = {
                "conversation_id": ka_conversation_id,
                "role": "assistant",
                "content": "თქვენი აღწერის მიხედვით, ხმაური შეიძლება გამოწვეული იყოს: 1) ზეთის დაბალი დონით, 2) სტარტერის პრობლემებით, 3) ზოლის მოწყვეტით. რეკომენდებული است ჯერ ზეთის დონე შეამოწმოთ.",
                "language": "ka",
                "is_automotive": True,
                "original_content": "Based on your description, the noise could be caused by: 1) low oil level, 2) starter issues, 3) belt problems. I recommend checking the oil level first."
            }
            
            ka_assistant_result = db.client.table('messages').insert(ka_assistant_message).execute()
            
            # Verify bilingual data integrity
            ka_messages = db.client.table('messages').select("*").eq('conversation_id', ka_conversation_id).execute()
            assert len(ka_messages.data) == 2
            assert ka_messages.data[0]['language'] == 'ka'
            assert ka_messages.data[1]['language'] == 'ka'
            assert ka_messages.data[1]['original_content'] is not None  # Has translation
            
        finally:
            # Cleanup
            db.client.table('conversations').delete().eq('id', ka_conversation_id).execute()
    
    def test_system_performance_integration(self):
        """Test that the complete system meets performance requirements"""
        import time
        
        start_time = time.time()
        
        # Full system initialization
        config_validation = Config.validate_required_env_vars()
        db = DatabaseService()
        health = db.health_check()
        
        initialization_time = time.time() - start_time
        assert initialization_time < 3.0, f"System initialization took {initialization_time:.2f}s, should be < 3s"
        
        # Full conversation workflow timing
        start_time = time.time()
        
        # Create conversation
        conversation_data = {
            "user_id": "performance_test_user",
            "language": "en",
            "status": "active"
        }
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        # Add message
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Performance test message",
            "language": "en"
        }
        db.client.table('messages').insert(message_data).execute()
        
        # Retrieve conversation with messages
        db.client.table('conversations').select("*").eq('id', conversation_id).execute()
        db.client.table('messages').select("*").eq('conversation_id', conversation_id).execute()
        
        workflow_time = time.time() - start_time
        assert workflow_time < 2.0, f"Conversation workflow took {workflow_time:.2f}s, should be < 2s"
        
        # Cleanup
        db.client.table('conversations').delete().eq('id', conversation_id).execute()
    
    def test_error_handling_integration(self):
        """Test error handling across the complete system"""
        # Test configuration error handling
        original_key = Config.OPENAI_API_KEY
        try:
            Config.OPENAI_API_KEY = "invalid_key"
            
            # Should detect invalid configuration
            with pytest.raises(Exception):
                openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                openai_client.models.list()  # This should fail
                
        finally:
            Config.OPENAI_API_KEY = original_key
        
        # Test database error handling
        db = DatabaseService()
        
        # Invalid conversation creation should not affect database state
        invalid_conversation = {
            "user_id": "error_test_user",
            "language": "invalid_language",  # Should fail constraint
            "status": "active"
        }
        
        with pytest.raises(Exception):
            db.client.table('conversations').insert(invalid_conversation).execute()
        
        # Database should still be healthy after error
        health = db.health_check()
        assert health["status"] == "healthy"
        
        # Valid operations should still work
        valid_conversation = {
            "user_id": "error_test_user",
            "language": "en",
            "status": "active"
        }
        
        result = db.client.table('conversations').insert(valid_conversation).execute()
        conversation_id = result.data[0]['id']
        
        # Cleanup
        db.client.table('conversations').delete().eq('id', conversation_id).execute()


class TestSystemReadiness:
    """Test that the system is ready for the next development phase"""
    
    def test_phase_1_completion_criteria(self):
        """Verify that Phase 1 (Database Foundation) completion criteria are met"""
        # 1. Configuration management working
        config_validation = Config.validate_required_env_vars()
        assert config_validation["status"] == "ok"
        
        # 2. Database connection established
        db = DatabaseService()
        health = db.health_check()
        assert health["status"] == "healthy"
        
        # 3. All required tables exist
        tables = db.get_tables()
        required_tables = ["conversations", "messages", "conversation_contexts"]
        for table in required_tables:
            assert table in tables
        
        # 4. CRUD operations working
        crud_result = db.test_crud_operations()
        assert crud_result["create"] is True
        assert crud_result["read"] is True
        assert crud_result["delete"] is True
        assert crud_result["error"] is None
        
        # 5. External API connections working
        openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        models = openai_client.models.list()
        assert len(models.data) > 0
        
        # 6. Bilingual support ready
        # Test both language constraints work
        for lang in ["en", "ka"]:
            test_conv = {
                "user_id": f"readiness_test_{lang}",
                "language": lang,
                "status": "active"
            }
            result = db.client.table('conversations').insert(test_conv).execute()
            conv_id = result.data[0]['id']
            # Cleanup
            db.client.table('conversations').delete().eq('id', conv_id).execute()
    
    def test_ready_for_phase_2(self):
        """Verify system is ready for Phase 2: OpenAI Integration"""
        # Database foundation must be solid
        db = DatabaseService()
        
        # Can create conversations for OpenAI integration
        conversation_data = {
            "user_id": "phase_2_readiness_test",
            "language": "en",
            "status": "active",
            "title": "Ready for OpenAI Integration"
        }
        
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        # Can store messages (needed for OpenAI conversation history)
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Test message for OpenAI integration readiness",
            "language": "en"
        }
        
        msg_result = db.client.table('messages').insert(message_data).execute()
        
        # Can store contexts (needed for OpenAI context compression)
        context_data = {
            "conversation_id": conversation_id,
            "compressed_context": '{"test": "ready for OpenAI integration"}',
            "message_count": 1,
            "is_active": True
        }
        
        ctx_result = db.client.table('conversation_contexts').insert(context_data).execute()
        
        # OpenAI credentials are valid
        openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        models = openai_client.models.list()
        model_ids = [model.id for model in models.data]
        
        # Should have GPT models available for chat
        assert any("gpt" in model_id.lower() for model_id in model_ids)
        
        # Should have access to moderation API (will be needed)
        try:
            moderation = openai_client.moderations.create(input="test input")
            assert moderation is not None
        except Exception as e:
            pytest.fail(f"Moderation API not accessible: {e}")
        
        # Cleanup
        db.client.table('conversations').delete().eq('id', conversation_id).execute() 