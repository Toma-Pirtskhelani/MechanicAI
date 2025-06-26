import pytest
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.database_service import DatabaseService


class TestConversationRepositoryBasics:
    """Test basic conversation repository operations"""
    
    def test_conversation_repository_initialization(self):
        """Test that conversation repository initializes correctly"""
        repo = ConversationRepository()
        assert repo is not None
        assert hasattr(repo, 'db_service')
        assert isinstance(repo.db_service, DatabaseService)
        
        # Test that database connection works through repository
        health = repo.db_service.health_check()
        assert health["status"] == "healthy"
        assert "conversations" in health["tables"]
    
    def test_create_conversation_basic(self):
        """Test creating a basic conversation"""
        repo = ConversationRepository()
        
        conversation_data = {
            "user_id": "test_user_basic",
            "language": "en",
            "title": "Test Basic Conversation"
        }
        
        conversation_id = repo.create_conversation(**conversation_data)
        assert conversation_id is not None
        assert isinstance(conversation_id, str)
        
        try:
            # Verify conversation was created correctly
            conversation = repo.get_conversation(conversation_id)
            assert conversation is not None
            assert conversation["user_id"] == "test_user_basic"
            assert conversation["language"] == "en"
            assert conversation["title"] == "Test Basic Conversation"
            assert conversation["status"] == "active"  # Default status
            assert conversation["created_at"] is not None
            assert conversation["updated_at"] is not None
            
        finally:
            # Cleanup
            repo.delete_conversation(conversation_id)
    
    def test_create_conversation_georgian(self):
        """Test creating conversation in Georgian"""
        repo = ConversationRepository()
        
        conversation_data = {
            "user_id": "test_user_ka",
            "language": "ka",
            "title": "ავტომობილის პრობლემა"
        }
        
        conversation_id = repo.create_conversation(**conversation_data)
        
        try:
            conversation = repo.get_conversation(conversation_id)
            assert conversation["language"] == "ka"
            assert conversation["title"] == "ავტომობილის პრობლემა"
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_get_conversation_not_found(self):
        """Test getting non-existent conversation returns None"""
        repo = ConversationRepository()
        fake_id = str(uuid.uuid4())
        
        conversation = repo.get_conversation(fake_id)
        assert conversation is None
    
    def test_update_conversation(self):
        """Test updating conversation details"""
        repo = ConversationRepository()
        
        # Create conversation
        conversation_id = repo.create_conversation(
            user_id="test_update_user",
            language="en",
            title="Original Title"
        )
        
        try:
            # Update conversation
            update_data = {
                "title": "Updated Title",
                "status": "closed"
            }
            success = repo.update_conversation(conversation_id, **update_data)
            assert success is True
            
            # Verify updates
            conversation = repo.get_conversation(conversation_id)
            assert conversation["title"] == "Updated Title"
            assert conversation["status"] == "closed"
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_delete_conversation(self):
        """Test deleting conversation"""
        repo = ConversationRepository()
        
        # Create conversation
        conversation_id = repo.create_conversation(
            user_id="test_delete_user",
            language="en"
        )
        
        # Verify exists
        conversation = repo.get_conversation(conversation_id)
        assert conversation is not None
        
        # Delete
        success = repo.delete_conversation(conversation_id)
        assert success is True
        
        # Verify deleted
        conversation = repo.get_conversation(conversation_id)
        assert conversation is None


class TestConversationRepositoryMessages:
    """Test message management within conversations"""
    
    def test_add_message_to_conversation(self):
        """Test adding messages to conversation"""
        repo = ConversationRepository()
        
        # Create conversation
        conversation_id = repo.create_conversation(
            user_id="test_message_user",
            language="en"
        )
        
        try:
            # Add user message
            message_id = repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content="My car engine is making noise",
                language="en",
                is_automotive=True
            )
            assert message_id is not None
            
            # Add assistant message
            assistant_message_id = repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content="Can you describe the type of noise?",
                language="en",
                is_automotive=True
            )
            assert assistant_message_id is not None
            
            # Get messages
            messages = repo.get_conversation_messages(conversation_id)
            assert len(messages) == 2
            
            # Verify message order (should be chronological)
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "My car engine is making noise"
            assert messages[1]["role"] == "assistant"
            assert messages[1]["content"] == "Can you describe the type of noise?"
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_add_bilingual_messages(self):
        """Test adding messages in both languages"""
        repo = ConversationRepository()
        
        conversation_id = repo.create_conversation(
            user_id="test_bilingual_user",
            language="ka"
        )
        
        try:
            # Add Georgian user message
            repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content="ჩემი მანქანის ძრავი ხმაურობს",
                language="ka",
                is_automotive=True
            )
            
            # Add English assistant response with Georgian translation
            repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content="რა ტიპის ხმაურია?",
                language="ka",
                original_content="What type of noise is it?",
                is_automotive=True
            )
            
            messages = repo.get_conversation_messages(conversation_id)
            assert len(messages) == 2
            assert messages[0]["language"] == "ka"
            assert messages[1]["language"] == "ka"
            assert messages[1]["original_content"] == "What type of noise is it?"
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_get_recent_messages(self):
        """Test getting recent messages with limit"""
        repo = ConversationRepository()
        
        conversation_id = repo.create_conversation(
            user_id="test_recent_user",
            language="en"
        )
        
        try:
            # Add 5 messages
            for i in range(5):
                repo.add_message(
                    conversation_id=conversation_id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Message {i + 1}",
                    language="en"
                )
            
            # Get recent 3 messages
            recent_messages = repo.get_recent_messages(conversation_id, limit=3)
            assert len(recent_messages) == 3
            
            # Should be most recent messages (messages 3, 4, 5)
            assert recent_messages[0]["content"] == "Message 3"
            assert recent_messages[1]["content"] == "Message 4"
            assert recent_messages[2]["content"] == "Message 5"
            
        finally:
            repo.delete_conversation(conversation_id)


class TestConversationRepositoryContext:
    """Test conversation context management"""
    
    def test_create_conversation_context(self):
        """Test creating and retrieving conversation context"""
        repo = ConversationRepository()
        
        conversation_id = repo.create_conversation(
            user_id="test_context_user",
            language="en"
        )
        
        try:
            # Create context
            compressed_context = '{"summary": "User has engine noise issue", "key_points": ["engine noise", "seeking diagnosis"]}'
            context_id = repo.create_conversation_context(
                conversation_id=conversation_id,
                compressed_context=compressed_context,
                message_count=10
            )
            assert context_id is not None
            
            # Get active context
            context = repo.get_active_context(conversation_id)
            assert context is not None
            assert context["compressed_context"] == compressed_context
            assert context["message_count"] == 10
            assert context["is_active"] is True
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_update_context_on_new_messages(self):
        """Test context management when adding new messages"""
        repo = ConversationRepository()
        
        conversation_id = repo.create_conversation(
            user_id="test_context_update_user",
            language="en"
        )
        
        try:
            # Create initial context
            context_id = repo.create_conversation_context(
                conversation_id=conversation_id,
                compressed_context='{"summary": "Initial context"}',
                message_count=5
            )
            
            # Add more messages
            for i in range(3):
                repo.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=f"New message {i}",
                    language="en"
                )
            
            # Update context to mark old one inactive and create new one
            new_context_id = repo.create_conversation_context(
                conversation_id=conversation_id,
                compressed_context='{"summary": "Updated context with new messages"}',
                message_count=8
            )
            
            # Deactivate old context
            repo.deactivate_context(context_id)
            
            # Should get the new active context
            active_context = repo.get_active_context(conversation_id)
            assert active_context["id"] == new_context_id
            assert active_context["message_count"] == 8
            
        finally:
            repo.delete_conversation(conversation_id)


class TestConversationRepositoryQueries:
    """Test complex queries and conversation retrieval"""
    
    def test_get_user_conversations(self):
        """Test getting all conversations for a user"""
        repo = ConversationRepository()
        user_id = "test_multi_conv_user"
        conversation_ids = []
        
        try:
            # Create multiple conversations for user
            for i in range(3):
                conv_id = repo.create_conversation(
                    user_id=user_id,
                    language="en",
                    title=f"Conversation {i + 1}"
                )
                conversation_ids.append(conv_id)
            
            # Create conversation for different user (should not appear)
            other_conv_id = repo.create_conversation(
                user_id="other_user",
                language="en",
                title="Other User Conversation"
            )
            conversation_ids.append(other_conv_id)
            
            # Get conversations for our test user
            user_conversations = repo.get_user_conversations(user_id)
            assert len(user_conversations) == 3
            
            # Verify all belong to correct user
            for conv in user_conversations:
                assert conv["user_id"] == user_id
            
            # Verify ordering (should be newest first)
            titles = [conv["title"] for conv in user_conversations]
            assert "Conversation 3" in titles
            assert "Conversation 2" in titles
            assert "Conversation 1" in titles
            
        finally:
            # Cleanup all conversations
            for conv_id in conversation_ids:
                repo.delete_conversation(conv_id)
    
    def test_get_conversation_with_context(self):
        """Test getting conversation with full context (messages + compressed context)"""
        repo = ConversationRepository()
        
        conversation_id = repo.create_conversation(
            user_id="test_full_context_user",
            language="en"
        )
        
        try:
            # Add some messages
            repo.add_message(conversation_id, "user", "Hello", "en")
            repo.add_message(conversation_id, "assistant", "Hi there", "en")
            
            # Add compressed context
            repo.create_conversation_context(
                conversation_id=conversation_id,
                compressed_context='{"previous": "Some previous conversation"}',
                message_count=2
            )
            
            # Get full conversation context
            full_context = repo.get_conversation_with_context(conversation_id)
            assert full_context is not None
            assert "conversation" in full_context
            assert "recent_messages" in full_context
            assert "compressed_context" in full_context
            
            assert full_context["conversation"]["id"] == conversation_id
            assert len(full_context["recent_messages"]) == 2
            assert full_context["compressed_context"] is not None
            
        finally:
            repo.delete_conversation(conversation_id)


class TestConversationRepositoryPerformance:
    """Test performance requirements for conversation repository"""
    
    def test_conversation_operations_performance(self):
        """Test that conversation operations meet performance requirements"""
        repo = ConversationRepository()
        
        # Test conversation creation performance
        start_time = time.time()
        conversation_id = repo.create_conversation(
            user_id="perf_test_user",
            language="en",
            title="Performance Test"
        )
        creation_time = time.time() - start_time
        assert creation_time < 3.0, f"Conversation creation took {creation_time:.2f}s, should be < 3s"
        
        try:
            # Test message addition performance
            start_time = time.time()
            for i in range(10):
                repo.add_message(
                    conversation_id=conversation_id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Performance test message {i}",
                    language="en"
                )
            message_addition_time = time.time() - start_time
            assert message_addition_time < 5.0, f"Adding 10 messages took {message_addition_time:.2f}s, should be < 5s"
            
            # Test retrieval performance
            start_time = time.time()
            conversation = repo.get_conversation_with_context(conversation_id)
            retrieval_time = time.time() - start_time
            assert retrieval_time < 3.0, f"Full context retrieval took {retrieval_time:.2f}s, should be < 3s"
            assert conversation is not None
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_concurrent_conversation_operations(self):
        """Test concurrent operations on conversations"""
        repo = ConversationRepository()
        
        def create_and_use_conversation(thread_id):
            """Create conversation and add messages in a thread"""
            conversation_id = repo.create_conversation(
                user_id=f"concurrent_user_{thread_id}",
                language="en",
                title=f"Concurrent Test {thread_id}"
            )
            
            # Add messages
            for i in range(3):
                repo.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=f"Thread {thread_id} message {i}",
                    language="en"
                )
            
            return conversation_id
        
        # Run concurrent operations
        num_threads = 5
        conversation_ids = []
        
        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(create_and_use_conversation, i) for i in range(num_threads)]
                
                for future in as_completed(futures):
                    conversation_id = future.result()
                    conversation_ids.append(conversation_id)
            
            # Verify all conversations exist and have correct data
            assert len(conversation_ids) == num_threads
            for i, conv_id in enumerate(conversation_ids):
                conversation = repo.get_conversation(conv_id)
                assert conversation is not None
                
                messages = repo.get_conversation_messages(conv_id)
                assert len(messages) == 3
                
        finally:
            # Cleanup
            for conv_id in conversation_ids:
                try:
                    repo.delete_conversation(conv_id)
                except:
                    pass


class TestConversationRepositoryErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_conversation_operations(self):
        """Test operations on invalid conversations"""
        repo = ConversationRepository()
        fake_id = str(uuid.uuid4())
        
        # Test operations on non-existent conversation
        assert repo.get_conversation(fake_id) is None
        assert repo.update_conversation(fake_id, title="New Title") is False
        assert repo.delete_conversation(fake_id) is False
        assert repo.get_conversation_messages(fake_id) == []
        assert repo.get_active_context(fake_id) is None
    
    def test_invalid_message_operations(self):
        """Test adding messages with invalid data"""
        repo = ConversationRepository()
        fake_conversation_id = str(uuid.uuid4())
        
        # Test adding message to non-existent conversation
        with pytest.raises(Exception):
            repo.add_message(
                conversation_id=fake_conversation_id,
                role="user",
                content="Test message",
                language="en"
            )
    
    def test_conversation_cascade_behavior(self):
        """Test that deleting conversation properly cascades to messages and contexts"""
        repo = ConversationRepository()
        
        conversation_id = repo.create_conversation(
            user_id="cascade_test_user",
            language="en"
        )
        
        # Add messages and context
        message_id = repo.add_message(conversation_id, "user", "Test message", "en")
        context_id = repo.create_conversation_context(
            conversation_id=conversation_id,
            compressed_context='{"test": "context"}',
            message_count=1
        )
        
        # Verify everything exists
        assert repo.get_conversation(conversation_id) is not None
        assert len(repo.get_conversation_messages(conversation_id)) == 1
        assert repo.get_active_context(conversation_id) is not None
        
        # Delete conversation
        success = repo.delete_conversation(conversation_id)
        assert success is True
        
        # Verify cascade deletion worked
        assert repo.get_conversation(conversation_id) is None
        assert len(repo.get_conversation_messages(conversation_id)) == 0
        assert repo.get_active_context(conversation_id) is None


class TestConversationRepositoryBilingualSupport:
    """Test bilingual conversation support"""
    
    def test_multilingual_conversation_handling(self):
        """Test handling conversations with mixed languages"""
        repo = ConversationRepository()
        
        # Create conversation in Georgian
        conversation_id = repo.create_conversation(
            user_id="bilingual_test_user",
            language="ka",
            title="ავტომობილის პრობლემა"
        )
        
        try:
            # Add Georgian user message
            repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content="ჩემი მანქანის ძრავი პრობლემას წარმოშობს",
                language="ka",
                is_automotive=True
            )
            
            # Add assistant response with translation
            repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content="შეგიძლიათ უფრო დეტალურად აღწეროთ პრობლემა?",
                language="ka",
                original_content="Can you describe the problem in more detail?",
                is_automotive=True
            )
            
            # Add user response in mixed content
            repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content="Engine-ს უცნაური ხმაური ემოსება",
                language="ka",
                is_automotive=True
            )
            
            messages = repo.get_conversation_messages(conversation_id)
            assert len(messages) == 3
            
            # Verify all messages preserved correctly
            assert messages[0]["language"] == "ka"
            assert "ძრავი" in messages[0]["content"]
            assert messages[1]["original_content"] == "Can you describe the problem in more detail?"
            assert "Engine" in messages[2]["content"] and "ხმაური" in messages[2]["content"]
            
        finally:
            repo.delete_conversation(conversation_id)
    
    def test_conversation_language_consistency(self):
        """Test that conversation language setting is maintained"""
        repo = ConversationRepository()
        
        for lang in ["en", "ka"]:
            conversation_id = repo.create_conversation(
                user_id=f"lang_test_user_{lang}",
                language=lang
            )
            
            try:
                conversation = repo.get_conversation(conversation_id)
                assert conversation["language"] == lang
                
                # Language should persist through updates
                repo.update_conversation(conversation_id, title="Updated Title")
                updated_conversation = repo.get_conversation(conversation_id)
                assert updated_conversation["language"] == lang
                
            finally:
                repo.delete_conversation(conversation_id)
