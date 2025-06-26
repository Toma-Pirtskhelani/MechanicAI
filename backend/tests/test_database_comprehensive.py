import pytest
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.db.database_service import DatabaseService


class TestDatabaseSchemaValidation:
    """Test that database schema matches our requirements"""
    
    def test_conversations_table_schema(self):
        """Test conversations table has correct schema"""
        db = DatabaseService()
        
        # Test table exists
        tables = db.get_tables()
        assert "conversations" in tables
        
        # Test we can insert with all required fields
        test_data = {
            "user_id": "schema_test_user",
            "language": "en",
            "title": "Schema Test Conversation",
            "status": "active"
        }
        
        result = db.client.table('conversations').insert(test_data).execute()
        assert result.data is not None
        assert len(result.data) == 1
        
        conversation = result.data[0]
        conversation_id = conversation['id']
        
        # Verify all fields are present and correct
        assert conversation['user_id'] == "schema_test_user"
        assert conversation['language'] == "en"
        assert conversation['title'] == "Schema Test Conversation"
        assert conversation['status'] == "active"
        assert conversation['id'] is not None
        assert conversation['created_at'] is not None
        assert conversation['updated_at'] is not None
        
        # Test language constraint (should only allow 'en' or 'ka')
        invalid_data = {
            "user_id": "schema_test_user",
            "language": "invalid_lang",
            "status": "active"
        }
        
        with pytest.raises(Exception) as exc_info:
            db.client.table('conversations').insert(invalid_data).execute()
        assert "constraint" in str(exc_info.value).lower() or "check" in str(exc_info.value).lower()
        
        # Test status constraint
        invalid_status_data = {
            "user_id": "schema_test_user", 
            "language": "en",
            "status": "invalid_status"
        }
        
        with pytest.raises(Exception) as exc_info:
            db.client.table('conversations').insert(invalid_status_data).execute()
        assert "constraint" in str(exc_info.value).lower() or "check" in str(exc_info.value).lower()
        
        # Cleanup
        db.client.table('conversations').delete().eq('id', conversation_id).execute()
    
    def test_messages_table_schema(self):
        """Test messages table has correct schema and foreign key constraints"""
        db = DatabaseService()
        
        # First create a conversation
        conversation_data = {
            "user_id": "message_test_user",
            "language": "en",
            "status": "active"
        }
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        try:
            # Test valid message insertion
            message_data = {
                "conversation_id": conversation_id,
                "role": "user",
                "content": "Test message content",
                "language": "en",
                "is_automotive": True
            }
            
            result = db.client.table('messages').insert(message_data).execute()
            assert result.data is not None
            message = result.data[0]
            message_id = message['id']
            
            # Verify all fields
            assert message['conversation_id'] == conversation_id
            assert message['role'] == "user"
            assert message['content'] == "Test message content"
            assert message['language'] == "en"
            assert message['is_automotive'] is True
            assert message['created_at'] is not None
            
            # Test role constraint
            invalid_role_data = {
                "conversation_id": conversation_id,
                "role": "invalid_role",
                "content": "Test",
                "language": "en"
            }
            
            with pytest.raises(Exception) as exc_info:
                db.client.table('messages').insert(invalid_role_data).execute()
            assert "constraint" in str(exc_info.value).lower() or "check" in str(exc_info.value).lower()
            
            # Test foreign key constraint (non-existent conversation)
            fake_conversation_id = str(uuid.uuid4())
            invalid_fk_data = {
                "conversation_id": fake_conversation_id,
                "role": "user",
                "content": "Test",
                "language": "en"
            }
            
            with pytest.raises(Exception) as exc_info:
                db.client.table('messages').insert(invalid_fk_data).execute()
            assert "foreign key" in str(exc_info.value).lower() or "violates" in str(exc_info.value).lower()
            
            # Cleanup message
            db.client.table('messages').delete().eq('id', message_id).execute()
            
        finally:
            # Cleanup conversation
            db.client.table('conversations').delete().eq('id', conversation_id).execute()
    
    def test_conversation_contexts_table_schema(self):
        """Test conversation_contexts table schema and constraints"""
        db = DatabaseService()
        
        # Create conversation first
        conversation_data = {
            "user_id": "context_test_user",
            "language": "en",
            "status": "active"
        }
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        try:
            # Test valid context insertion
            context_data = {
                "conversation_id": conversation_id,
                "compressed_context": '{"summary": "Test conversation about car engine", "key_points": ["engine issue", "oil leak"]}',
                "message_count": 5,
                "is_active": True
            }
            
            result = db.client.table('conversation_contexts').insert(context_data).execute()
            assert result.data is not None
            context = result.data[0]
            context_id = context['id']
            
            # Verify all fields
            assert context['conversation_id'] == conversation_id
            assert context['compressed_context'] == context_data['compressed_context']
            assert context['message_count'] == 5
            assert context['is_active'] is True
            assert context['created_at'] is not None
            
            # Cleanup
            db.client.table('conversation_contexts').delete().eq('id', context_id).execute()
            
        finally:
            # Cleanup conversation
            db.client.table('conversations').delete().eq('id', conversation_id).execute()


class TestDatabaseConcurrencyAndPerformance:
    """Test database behavior under concurrent access and performance requirements"""
    
    def test_concurrent_conversation_creation(self):
        """Test multiple concurrent conversation creations"""
        db = DatabaseService()
        
        def create_conversation(thread_id):
            """Create a conversation in a thread"""
            conversation_data = {
                "user_id": f"concurrent_test_user_{thread_id}",
                "language": "en",
                "status": "active",
                "title": f"Concurrent Test {thread_id}"
            }
            result = db.client.table('conversations').insert(conversation_data).execute()
            return result.data[0]['id']
        
        # Create 5 conversations concurrently
        num_threads = 5
        conversation_ids = []
        
        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(create_conversation, i) for i in range(num_threads)]
                
                for future in as_completed(futures):
                    conversation_id = future.result()
                    conversation_ids.append(conversation_id)
            
            # Verify all conversations were created
            assert len(conversation_ids) == num_threads
            assert len(set(conversation_ids)) == num_threads  # All unique
            
            # Verify they all exist in database
            for conv_id in conversation_ids:
                result = db.client.table('conversations').select("*").eq('id', conv_id).execute()
                assert len(result.data) == 1
                
        finally:
            # Cleanup all conversations
            for conv_id in conversation_ids:
                try:
                    db.client.table('conversations').delete().eq('id', conv_id).execute()
                except:
                    pass  # Ignore cleanup errors
    
    def test_database_performance_requirements(self):
        """Test that database operations meet performance requirements"""
        db = DatabaseService()
        
        # Test connection speed
        start_time = time.time()
        health = db.health_check()
        connection_time = time.time() - start_time
        
        assert health["status"] == "healthy"
        assert connection_time < 5.0, f"Database connection took {connection_time:.2f}s, should be < 5s"
        
        # Test query performance
        start_time = time.time()
        result = db.client.table('conversations').select("*").limit(10).execute()
        query_time = time.time() - start_time
        
        assert query_time < 3.0, f"Simple query took {query_time:.2f}s, should be < 3s"
        
        # Test CRUD operation performance
        start_time = time.time()
        crud_result = db.test_crud_operations()
        crud_time = time.time() - start_time
        
        assert crud_result["error"] is None
        assert crud_time < 5.0, f"CRUD operations took {crud_time:.2f}s, should be < 5s"
    
    def test_large_data_handling(self):
        """Test handling of larger conversation contexts"""
        db = DatabaseService()
        
        # Create conversation
        conversation_data = {
            "user_id": "large_data_test",
            "language": "en",
            "status": "active"
        }
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        try:
            # Create a large context (simulating long conversation)
            large_context = {
                "summary": "Very long conversation about automotive issues",
                "messages": [{"role": "user", "content": f"Message {i} about car problems"} for i in range(100)],
                "key_points": [f"Point {i}" for i in range(50)]
            }
            
            context_data = {
                "conversation_id": conversation_id,
                "compressed_context": str(large_context),  # Convert to string
                "message_count": 100,
                "is_active": True
            }
            
            # Should handle large context without issues
            result = db.client.table('conversation_contexts').insert(context_data).execute()
            assert result.data is not None
            context_id = result.data[0]['id']
            
            # Should be able to retrieve it
            retrieved = db.client.table('conversation_contexts').select("*").eq('id', context_id).execute()
            assert len(retrieved.data) == 1
            assert retrieved.data[0]['message_count'] == 100
            
            # Cleanup
            db.client.table('conversation_contexts').delete().eq('id', context_id).execute()
            
        finally:
            # Cleanup conversation
            db.client.table('conversations').delete().eq('id', conversation_id).execute()


class TestDatabaseDataIntegrity:
    """Test data integrity and cascade behavior"""
    
    def test_cascade_delete_behavior(self):
        """Test that deleting a conversation cascades to messages and contexts"""
        db = DatabaseService()
        
        # Create conversation
        conversation_data = {
            "user_id": "cascade_test_user",
            "language": "en",
            "status": "active"
        }
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        # Create messages
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Test message for cascade",
            "language": "en"
        }
        msg_result = db.client.table('messages').insert(message_data).execute()
        message_id = msg_result.data[0]['id']
        
        # Create context
        context_data = {
            "conversation_id": conversation_id,
            "compressed_context": '{"test": "cascade context"}',
            "message_count": 1,
            "is_active": True
        }
        ctx_result = db.client.table('conversation_contexts').insert(context_data).execute()
        context_id = ctx_result.data[0]['id']
        
        # Verify all exist
        conv_check = db.client.table('conversations').select("*").eq('id', conversation_id).execute()
        msg_check = db.client.table('messages').select("*").eq('id', message_id).execute()
        ctx_check = db.client.table('conversation_contexts').select("*").eq('id', context_id).execute()
        
        assert len(conv_check.data) == 1
        assert len(msg_check.data) == 1
        assert len(ctx_check.data) == 1
        
        # Delete conversation (should cascade)
        db.client.table('conversations').delete().eq('id', conversation_id).execute()
        
        # Verify cascade worked
        conv_check_after = db.client.table('conversations').select("*").eq('id', conversation_id).execute()
        msg_check_after = db.client.table('messages').select("*").eq('id', message_id).execute()
        ctx_check_after = db.client.table('conversation_contexts').select("*").eq('id', context_id).execute()
        
        assert len(conv_check_after.data) == 0  # Conversation deleted
        assert len(msg_check_after.data) == 0   # Messages cascaded
        assert len(ctx_check_after.data) == 0   # Contexts cascaded
    
    def test_bilingual_data_integrity(self):
        """Test data integrity for bilingual (Georgian/English) content"""
        db = DatabaseService()
        
        # Test both languages
        for language in ["en", "ka"]:
            conversation_data = {
                "user_id": f"bilingual_test_{language}",
                "language": language,
                "status": "active",
                "title": "ავტომობილის პრობლემა" if language == "ka" else "Car Problem"
            }
            
            conv_result = db.client.table('conversations').insert(conversation_data).execute()
            conversation_id = conv_result.data[0]['id']
            
            try:
                # Test message in same language
                message_content = "რა პრობლემაა ძრავთან?" if language == "ka" else "What's wrong with the engine?"
                message_data = {
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": message_content,
                    "language": language
                }
                
                msg_result = db.client.table('messages').insert(message_data).execute()
                message_id = msg_result.data[0]['id']
                
                # Verify content preserved correctly
                retrieved = db.client.table('messages').select("*").eq('id', message_id).execute()
                assert retrieved.data[0]['content'] == message_content
                assert retrieved.data[0]['language'] == language
                
                # Cleanup
                db.client.table('messages').delete().eq('id', message_id).execute()
                
            finally:
                # Cleanup conversation
                db.client.table('conversations').delete().eq('id', conversation_id).execute()


class TestDatabaseErrorRecovery:
    """Test database error handling and recovery scenarios"""
    
    def test_connection_retry_behavior(self):
        """Test that database service can recover from connection issues"""
        db = DatabaseService()
        
        # First verify normal connection works
        health1 = db.health_check()
        assert health1["status"] == "healthy"
        
        # Create a new service instance to test fresh connection
        db2 = DatabaseService()
        health2 = db2.health_check()
        assert health2["status"] == "healthy"
        
        # Both should work independently
        assert health1["tables"] == health2["tables"]
    
    def test_transaction_consistency(self):
        """Test that failed operations don't leave partial data"""
        db = DatabaseService()
        
        # Create a conversation
        conversation_data = {
            "user_id": "transaction_test_user",
            "language": "en",
            "status": "active"
        }
        conv_result = db.client.table('conversations').insert(conversation_data).execute()
        conversation_id = conv_result.data[0]['id']
        
        try:
            # Try to create a message with invalid data that should fail
            invalid_message_data = {
                "conversation_id": conversation_id,
                "role": "invalid_role",  # This should fail
                "content": "Test message",
                "language": "en"
            }
            
            # This should fail
            with pytest.raises(Exception):
                db.client.table('messages').insert(invalid_message_data).execute()
            
            # Verify no partial message was created
            messages = db.client.table('messages').select("*").eq('conversation_id', conversation_id).execute()
            assert len(messages.data) == 0, "No partial message should have been created"
            
            # Conversation should still exist and be intact
            conversations = db.client.table('conversations').select("*").eq('id', conversation_id).execute()
            assert len(conversations.data) == 1
            assert conversations.data[0]['status'] == 'active'
            
        finally:
            # Cleanup
            db.client.table('conversations').delete().eq('id', conversation_id).execute() 