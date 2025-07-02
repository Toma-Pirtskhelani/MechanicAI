"""
Chat endpoint implementation for MechaniAI API.
Provides REST endpoints for automotive conversation and history retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
import logging
import time
import sys
import os
import re
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from app.core.chat_service import ChatService
from app.db.repositories.conversation_repository import ConversationRepository

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="Unique user identifier")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID for continuity")
    language: str = Field("en", description="User language preference (en/ka)")
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code."""
        if v not in ['en', 'ka']:
            raise ValueError('Language must be "en" or "ka"')
        return v
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate and sanitize message content."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        
        # Sanitize the message
        sanitized = cls._sanitize_input(v.strip())
        
        # Check for extremely repetitive content (potential spam)
        if cls._is_repetitive_content(sanitized):
            raise ValueError('Message contains excessive repetitive content')
        
        return sanitized
    
    @field_validator('user_id')
    @classmethod  
    def validate_user_id(cls, v):
        """Validate and sanitize user ID."""
        if not v or not v.strip():
            raise ValueError('User ID cannot be empty or whitespace only')
        
        # Sanitize user ID
        sanitized = cls._sanitize_input(v.strip())
        
        # Check for valid format (alphanumeric, underscores, hyphens only)
        if not re.match(r'^[a-zA-Z0-9_-]+$', sanitized):
            raise ValueError('User ID can only contain letters, numbers, underscores, and hyphens')
        
        return sanitized
    
    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v):
        """Validate conversation ID format if provided."""
        if v is None:
            return v
        
        if not v.strip():
            raise ValueError('Conversation ID cannot be empty if provided')
        
        # Sanitize conversation ID
        sanitized = cls._sanitize_input(v.strip())
        
        # Basic UUID-like format check (flexible to accommodate different ID formats)
        if not re.match(r'^[a-zA-Z0-9_-]+$', sanitized):
            raise ValueError('Invalid conversation ID format')
        
        return sanitized
    
    @staticmethod
    def _sanitize_input(text: str) -> str:
        """Sanitize input text to prevent injection attacks."""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove or escape potentially dangerous characters
        # Remove CRLF injection attempts
        text = text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def _is_repetitive_content(text: str) -> bool:
        """Check if content is excessively repetitive (potential spam)."""
        words = text.split()
        if len(words) < 10:
            return False
        
        # Check for same word repeated many times
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
            if word_counts[word] > len(words) * 0.5:  # Same word > 50% of content
                return True
        
        return False


class PerformanceMetrics(BaseModel):
    """Performance metrics for response."""
    response_time_ms: int = Field(..., description="Total response time in milliseconds")
    service_times: Dict[str, int] = Field(default={}, description="Individual service response times")


class ContextEnhancement(BaseModel):
    """Context enhancement information."""
    vehicle_info: Dict[str, Any] = Field(default={}, description="Extracted vehicle information")
    symptoms: List[str] = Field(default=[], description="Identified symptoms")
    diagnostic_codes: List[str] = Field(default=[], description="Extracted diagnostic codes")
    safety_priority: str = Field(default="normal", description="Safety assessment priority")
    predicted_issues: List[str] = Field(default=[], description="Predicted automotive issues")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="AI assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    language: str = Field(..., description="Response language")
    context_enhancement: ContextEnhancement = Field(..., description="Enhanced context information")
    performance_metrics: PerformanceMetrics = Field(..., description="Performance information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ConversationSummary(BaseModel):
    """Summary model for conversation history."""
    id: str = Field(..., description="Conversation ID")
    created_at: datetime = Field(..., description="Conversation creation time")
    last_message_at: datetime = Field(..., description="Last message timestamp")
    message_count: int = Field(..., description="Number of messages in conversation")
    preview: str = Field(..., description="Preview of the conversation")


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history endpoint."""
    conversations: List[ConversationSummary] = Field(..., description="List of user conversations")
    total_count: int = Field(..., description="Total number of conversations")
    user_id: str = Field(..., description="User identifier")


# Dependency injection
def get_chat_service() -> ChatService:
    """Get ChatService instance."""
    return ChatService()


def get_conversation_repository() -> ConversationRepository:
    """Get ConversationRepository instance."""
    return ConversationRepository()


# Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Process user message and generate automotive expert response.
    
    Args:
        request: Chat request with message, user ID, and language preference
        chat_service: ChatService dependency for conversation processing
        
    Returns:
        ChatResponse: AI response with context enhancement and performance metrics
        
    Raises:
        HTTPException: For validation errors, service failures, or invalid requests
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing chat request for user {request.user_id}, language: {request.language}")
        
        # Process the conversation
        if request.conversation_id:
            # Continue existing conversation
            result = chat_service.process_message(
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                message=request.message,
                language=request.language
            )
        else:
            # Start new conversation
            result = chat_service.start_conversation(
                user_id=request.user_id,
                initial_message=request.message,
                language=request.language
            )
        
        # Calculate performance metrics
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # For now, create basic context enhancement (can be enhanced later)
        # This would typically be extracted from the ChatService or context enhancement service
        context_enhancement = ContextEnhancement(
            vehicle_info={},
            symptoms=[],
            diagnostic_codes=[],
            safety_priority="normal",
            predicted_issues=[]
        )
        
        # Create performance metrics
        performance_metrics = PerformanceMetrics(
            response_time_ms=total_time_ms,
            service_times={}
        )
        
        # Create response
        response = ChatResponse(
            response=result['response'],
            conversation_id=result['conversation_id'],
            language=request.language,  # Use request language since result may not include it
            context_enhancement=context_enhancement,
            performance_metrics=performance_metrics
        )
        
        logger.info(f"Chat request processed successfully in {total_time_ms}ms")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in chat endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while processing your request"
        )


@router.get("/conversations/{user_id}", response_model=ConversationHistoryResponse)
async def get_user_conversations(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    conversation_repo: ConversationRepository = Depends(get_conversation_repository)
):
    """
    Retrieve conversation history for a specific user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of conversations to return (default: 20)
        offset: Number of conversations to skip (default: 0)
        conversation_repo: ConversationRepository dependency
        
    Returns:
        ConversationHistoryResponse: List of user conversations with metadata
        
    Raises:
        HTTPException: For invalid user ID or service failures
    """
    try:
        logger.info(f"Retrieving conversation history for user {user_id}")
        
        # Validate user_id
        if not user_id.strip():
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        
        # Get conversations from repository
        conversations_data = conversation_repo.get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        conversations = []
        for conv_data in conversations_data:
            conversation_summary = ConversationSummary(
                id=conv_data['id'],
                created_at=conv_data['created_at'],
                last_message_at=conv_data.get('last_message_at', conv_data['created_at']),
                message_count=conv_data.get('message_count', 0),
                preview=conv_data.get('preview', 'Automotive conversation')[:100]
            )
            conversations.append(conversation_summary)
        
        # Get total count
        total_count = conversation_repo.count_user_conversations(user_id)
        
        response = ConversationHistoryResponse(
            conversations=conversations,
            total_count=total_count,
            user_id=user_id
        )
        
        logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in conversation history endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving conversation history"
        ) 