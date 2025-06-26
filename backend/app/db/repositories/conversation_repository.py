from typing import List, Dict, Any, Optional
import logging
from app.db.database_service import DatabaseService

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for managing conversations, messages, and contexts"""
    
    def __init__(self):
        """Initialize conversation repository with database service"""
        self.db_service = DatabaseService()
    
    # Conversation CRUD Operations
    
    def create_conversation(self, user_id: str, language: str, title: Optional[str] = None, status: str = "active") -> Optional[str]:
        """
        Create a new conversation
        
        Args:
            user_id: ID of the user starting the conversation
            language: Language code ('en' or 'ka')
            title: Optional conversation title
            status: Conversation status ('active' or 'closed')
            
        Returns:
            Conversation ID if successful, None otherwise
        """
        try:
            conversation_data = {
                "user_id": user_id,
                "language": language,
                "status": status
            }
            
            if title:
                conversation_data["title"] = title
            
            result = self.db_service.client.table('conversations').insert(conversation_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation data dict or None if not found
        """
        try:
            result = self.db_service.client.table('conversations').select("*").eq('id', conversation_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None
    
    def update_conversation(self, conversation_id: str, **kwargs) -> bool:
        """
        Update conversation with new data
        
        Args:
            conversation_id: ID of the conversation
            **kwargs: Fields to update (title, status, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First check if conversation exists
            existing = self.get_conversation(conversation_id)
            if not existing:
                return False
            
            # Prepare update data (filter out None values)
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            
            if not update_data:
                return True  # Nothing to update
            
            result = self.db_service.client.table('conversations').update(update_data).eq('id', conversation_id).execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation (cascades to messages and contexts)
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if conversation exists first
            existing = self.get_conversation(conversation_id)
            if not existing:
                return False
            
            result = self.db_service.client.table('conversations').delete().eq('id', conversation_id).execute()
            
            return True  # Supabase doesn't return data on delete, so assume success if no exception
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dicts, ordered by most recent first
        """
        try:
            result = self.db_service.client.table('conversations')\
                .select("*")\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            return []
    
    # Message Operations
    
    def add_message(self, conversation_id: str, role: str, content: str, language: str, 
                   original_content: Optional[str] = None, is_automotive: Optional[bool] = None) -> Optional[str]:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            role: Message role ('user' or 'assistant')
            content: Message content
            language: Language code ('en' or 'ka')
            original_content: Original content before translation (optional)
            is_automotive: Whether message is automotive-related (optional)
            
        Returns:
            Message ID if successful, None otherwise
        """
        try:
            message_data = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "language": language
            }
            
            if original_content is not None:
                message_data["original_content"] = original_content
            
            if is_automotive is not None:
                message_data["is_automotive"] = is_automotive
            
            result = self.db_service.client.table('messages').insert(message_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise  # Re-raise to allow tests to catch foreign key violations
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of message dicts, ordered chronologically
        """
        try:
            result = self.db_service.client.table('messages')\
                .select("*")\
                .eq('conversation_id', conversation_id)\
                .order('created_at', desc=False)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            return []
    
    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent messages for a conversation
        
        Args:
            conversation_id: ID of the conversation
            limit: Number of recent messages to return
            
        Returns:
            List of recent message dicts, ordered chronologically
        """
        try:
            # Get recent messages (newest first, then reverse for chronological order)
            result = self.db_service.client.table('messages')\
                .select("*")\
                .eq('conversation_id', conversation_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            messages = result.data if result.data else []
            
            # Reverse to get chronological order (oldest first)
            messages.reverse()
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages for conversation {conversation_id}: {e}")
            return []
    
    # Context Operations
    
    def create_conversation_context(self, conversation_id: str, compressed_context: str, 
                                  message_count: int) -> Optional[str]:
        """
        Create compressed context for conversation
        
        Args:
            conversation_id: ID of the conversation
            compressed_context: Compressed conversation context (JSON string)
            message_count: Number of messages this context represents
            
        Returns:
            Context ID if successful, None otherwise
        """
        try:
            context_data = {
                "conversation_id": conversation_id,
                "compressed_context": compressed_context,
                "message_count": message_count,
                "is_active": True
            }
            
            result = self.db_service.client.table('conversation_contexts').insert(context_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating context for conversation {conversation_id}: {e}")
            return None
    
    def get_active_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active compressed context for conversation
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Context data dict or None if not found
        """
        try:
            result = self.db_service.client.table('conversation_contexts')\
                .select("*")\
                .eq('conversation_id', conversation_id)\
                .eq('is_active', True)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting active context for conversation {conversation_id}: {e}")
            return None
    
    def deactivate_context(self, context_id: str) -> bool:
        """
        Mark a context as inactive
        
        Args:
            context_id: ID of the context
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db_service.client.table('conversation_contexts')\
                .update({"is_active": False})\
                .eq('id', context_id)\
                .execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Error deactivating context {context_id}: {e}")
            return False
    
    # Complex Queries
    
    def get_conversation_with_context(self, conversation_id: str, recent_message_limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get conversation with full context (conversation + recent messages + compressed context)
        
        Args:
            conversation_id: ID of the conversation
            recent_message_limit: Number of recent messages to include
            
        Returns:
            Dict with 'conversation', 'recent_messages', and 'compressed_context' keys
        """
        try:
            # Get conversation
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Get recent messages
            recent_messages = self.get_recent_messages(conversation_id, recent_message_limit)
            
            # Get active compressed context
            compressed_context = self.get_active_context(conversation_id)
            
            return {
                "conversation": conversation,
                "recent_messages": recent_messages,
                "compressed_context": compressed_context
            }
            
        except Exception as e:
            logger.error(f"Error getting full context for conversation {conversation_id}: {e}")
            return None 