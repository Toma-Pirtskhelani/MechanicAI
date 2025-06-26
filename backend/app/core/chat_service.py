"""
Chat Service - Core conversation flow orchestration for MechaniAI

This service integrates all Phase 2 AI services to provide complete
automotive assistant functionality with bilingual support.
"""

import logging
from typing import Dict, Any, List, Optional
from app.services.openai_service import OpenAIService
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.database_service import DatabaseService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Core chat service that orchestrates the complete conversation flow.
    
    Integrates:
    - Content moderation
    - Automotive relevance filtering
    - Expert response generation
    - Context compression
    - Translation services
    - Conversation management
    """
    
    def __init__(self):
        """Initialize chat service with all required dependencies"""
        self.openai_service = OpenAIService()
        self.conversation_repo = ConversationRepository()
        self.db_service = DatabaseService()
        
        # Configuration
        self.max_messages_before_compression = 10
        self.supported_languages = {'en', 'ka'}  # English and Georgian
        
        logger.info("ChatService initialized with all dependencies")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all service dependencies
        
        Returns:
            Dict with health status of all services
        """
        try:
            # Check OpenAI service
            openai_status = self.openai_service.health_check()
            openai_healthy = openai_status.get('api_accessible', False)
            
            # Check database service
            db_status = self.db_service.health_check()
            db_healthy = db_status.get('status') == 'healthy'
            
            overall_healthy = openai_healthy and db_healthy
            
            return {
                'openai_service': openai_healthy,
                'database_service': db_healthy,
                'overall_status': overall_healthy
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'openai_service': False,
                'database_service': False,
                'overall_status': False,
                'error': str(e)
            }
    
    def start_conversation(self, user_id: str, initial_message: str, language: str) -> Dict[str, Any]:
        """
        Start a new conversation with the automotive assistant
        
        Args:
            user_id: Unique identifier for the user
            initial_message: First message from the user
            language: Language code ('en' or 'ka')
            
        Returns:
            Dict with conversation_id, response, and language
            
        Raises:
            ValueError: If input validation fails
        """
        try:
            # Input validation
            self._validate_inputs(user_id, initial_message, language)
            
            # Create new conversation
            conversation_id = self.conversation_repo.create_conversation(
                user_id=user_id,
                language=language,
                title=self._generate_conversation_title(initial_message),
                status="active"
            )
            
            if not conversation_id:
                raise ValueError("Failed to create conversation")
            
            # Process the initial message
            response = self._process_message_flow(
                user_id=user_id,
                conversation_id=conversation_id,
                message=initial_message,
                language=language,
                is_initial=True
            )
            
            return {
                'conversation_id': conversation_id,
                'response': response['response'],
                'language': language
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation for user {user_id}: {e}")
            raise
    
    def process_message(self, user_id: str, conversation_id: str, message: str, language: str) -> Dict[str, Any]:
        """
        Process a message in an existing conversation
        
        Args:
            user_id: Unique identifier for the user
            conversation_id: ID of the existing conversation
            message: User message to process
            language: Language code ('en' or 'ka')
            
        Returns:
            Dict with response and conversation_id
            
        Raises:
            ValueError: If conversation doesn't exist or input validation fails
        """
        try:
            # Input validation
            self._validate_inputs(user_id, message, language)
            
            # Verify conversation exists and belongs to user
            conversation = self.conversation_repo.get_conversation(conversation_id)
            if not conversation or conversation['user_id'] != user_id:
                raise ValueError(f"Conversation {conversation_id} not found for user {user_id}")
            
            # Process the message
            response = self._process_message_flow(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                language=language,
                is_initial=False
            )
            
            return {
                'conversation_id': conversation_id,
                'response': response['response']
            }
            
        except Exception as e:
            logger.error(f"Error processing message for conversation {conversation_id}: {e}")
            raise
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the complete conversation history
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of messages in chronological order
        """
        try:
            return self.conversation_repo.get_conversation_messages(conversation_id)
        except Exception as e:
            logger.error(f"Error getting conversation history for {conversation_id}: {e}")
            raise
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of user conversations
        """
        try:
            return self.conversation_repo.get_user_conversations(user_id)
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            raise
    
    def _process_message_flow(self, user_id: str, conversation_id: str, message: str, 
                            language: str, is_initial: bool) -> Dict[str, Any]:
        """
        Process message through the complete conversation flow
        
        This method orchestrates:
        1. Content moderation
        2. Automotive relevance check
        3. Context retrieval and enhancement
        4. Expert response generation
        5. Message storage
        6. Context compression (if needed)
        7. Translation (if needed)
        """
        try:
            # Step 1: Content Moderation
            logger.info(f"Step 1: Content moderation for conversation {conversation_id}")
            moderation_result = self.openai_service.moderate_content(message)
            
            if not moderation_result['safe']:
                # Store the rejected message for audit
                self.conversation_repo.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    language=language
                )
                
                safety_response = self._generate_safety_response(language)
                
                self.conversation_repo.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=safety_response,
                    language=language
                )
                
                return {'response': safety_response}
            
            # Step 2: Context Retrieval and Enhancement (moved before relevance check)
            logger.info(f"Step 2: Context retrieval for conversation {conversation_id}")
            conversation_context = self._get_enhanced_context(conversation_id)
            
            # Step 3: Automotive Relevance Check
            logger.info(f"Step 3: Automotive relevance check for conversation {conversation_id}")
            # For continuing conversations, if we have context, consider it automotive
            # since they already started an automotive conversation
            if not is_initial and conversation_context:
                # If this is a follow-up and we have conversation history, assume automotive
                relevance_result = {'is_automotive': True, 'confidence': 0.9, 'reasoning': 'Follow-up in automotive conversation'}
            else:
                relevance_result = self.openai_service.check_automotive_relevance(message)
            
            if not relevance_result['is_automotive']:
                # Store the message
                self.conversation_repo.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    language=language
                )
                
                redirect_response = self._generate_redirect_response(language)
                
                self.conversation_repo.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=redirect_response,
                    language=language
                )
                
                return {'response': redirect_response}
            
            # Step 4: Store user message
            self.conversation_repo.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
                language=language
            )
            
            # Step 5: Generate Expert Response
            logger.info(f"Step 5: Expert response generation for conversation {conversation_id}")
            expert_response = self.openai_service.generate_expert_response(
                query=message,
                conversation_history=conversation_context
            )
            
            # Step 6: Store assistant response
            self.conversation_repo.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=expert_response['response'],
                language=language
            )
            
            # Step 7: Check if context compression is needed
            logger.info(f"Step 7: Context compression check for conversation {conversation_id}")
            self._handle_context_compression(conversation_id)
            
            # Step 8: Translation (if needed)
            final_response = expert_response['response']
            if language != 'en':  # Translate if not English
                logger.info(f"Step 8: Translation to {language} for conversation {conversation_id}")
                translation_result = self.openai_service.auto_translate_response(
                    user_query=message,
                    system_response=final_response
                )
                final_response = translation_result.get('translated_response', final_response)
            
            return {'response': final_response}
            
        except Exception as e:
            logger.error(f"Error in message flow for conversation {conversation_id}: {e}")
            raise
    
    def _get_enhanced_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get enhanced conversation context including compressed history
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Enhanced context messages for the conversation
        """
        try:
            # Get recent messages
            recent_messages = self.conversation_repo.get_recent_messages(
                conversation_id, 
                limit=5  # Last 5 messages for immediate context
            )
            
            # Get compressed context if available
            compressed_context = self.conversation_repo.get_active_context(conversation_id)
            
            enhanced_context = []
            
            # Add compressed context if available
            if compressed_context:
                enhanced_context.append({
                    'role': 'system',
                    'content': f"Previous conversation summary: {compressed_context['compressed_context']}"
                })
            
            # Add recent messages
            enhanced_context.extend(recent_messages)
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error getting enhanced context for conversation {conversation_id}: {e}")
            return []
    
    def _handle_context_compression(self, conversation_id: str) -> None:
        """
        Handle context compression if the conversation has grown too long
        
        Args:
            conversation_id: ID of the conversation to potentially compress
        """
        try:
            # Get all messages for the conversation
            all_messages = self.conversation_repo.get_conversation_messages(conversation_id)
            
            # Check if compression is needed
            if len(all_messages) >= self.max_messages_before_compression:
                logger.info(f"Compressing context for conversation {conversation_id} ({len(all_messages)} messages)")
                
                # Compress the conversation
                compression_result = self.openai_service.compress_conversation_context(all_messages)
                
                # Deactivate previous context if it exists
                previous_context = self.conversation_repo.get_active_context(conversation_id)
                if previous_context:
                    self.conversation_repo.deactivate_context(previous_context['id'])
                
                # Store new compressed context
                self.conversation_repo.create_conversation_context(
                    conversation_id=conversation_id,
                    compressed_context=compression_result['compressed_context'],
                    message_count=len(all_messages)
                )
                
                logger.info(f"Context compression completed for conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error handling context compression for conversation {conversation_id}: {e}")
    
    def _validate_inputs(self, user_id: str, message: str, language: str) -> None:
        """
        Validate input parameters
        
        Args:
            user_id: User identifier to validate
            message: Message content to validate
            language: Language code to validate
            
        Raises:
            ValueError: If any input is invalid
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}. Supported: {self.supported_languages}")
        
        if len(message) > 5000:  # Reasonable message length limit
            raise ValueError("Message too long (max 5000 characters)")
    
    def _generate_conversation_title(self, initial_message: str) -> str:
        """
        Generate a title for the conversation based on the initial message
        
        Args:
            initial_message: First message from the user
            
        Returns:
            Generated conversation title
        """
        # Simple title generation - take first 50 characters
        title = initial_message.strip()[:50]
        if len(initial_message) > 50:
            title += "..."
        
        return title
    
    def _generate_safety_response(self, language: str) -> str:
        """
        Generate a safety response for inappropriate content
        
        Args:
            language: Language for the response
            
        Returns:
            Safety response message
        """
        if language == 'ka':
            return ("ვწუხვარ, ვერ შემიძლია ამ შინაარსზე პასუხის გაცემა. "
                   "გთხოვთ, დასვათ საკითხი, რომელიც დაკავშირებულია ავტომობილებთან ან ტექნიკურ პრობლემებთან.")
        else:
            return ("I'm sorry, but I cannot respond to that content. "
                   "Please ask questions related to automotive issues or technical problems with your vehicle.")
    
    def _generate_redirect_response(self, language: str) -> str:
        """
        Generate a polite redirect response for non-automotive queries
        
        Args:
            language: Language for the response
            
        Returns:
            Redirect response message
        """
        if language == 'ka':
            return ("ვარ Tegeta Motors-ის ავტომობილური ასისტენტი და ვეხმარები მხოლოდ მანქანებთან დაკავშირებულ საკითხებში. "
                   "გთხოვთ, დამისვათ კითხვა თქვენი ავტომობილის ტექნიკური პრობლემების, ტოის, დიაგნოსტიკის ან "
                   "სამუშაოების შესახებ. როგორ შემიძლია დაგეხმაროთ თქვენი მანქანის მდგომარეობის გაუმჯობესებაში?")
        else:
            return ("I'm Tegeta Motors' automotive assistant and I help only with car-related questions. "
                   "Please ask me about your vehicle's technical problems, maintenance, diagnostics, or repairs. "
                   "How can I help you with your car today?") 