from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
from app.config import config

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI service with client and default settings"""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.default_model = config.OPENAI_MODEL
        self.default_temperature = 0.7
        self.default_max_tokens = 1000
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check OpenAI API health and connectivity
        
        Returns:
            Dict with health status information
        """
        try:
            # Test API connectivity with a minimal request
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            
            return {
                "status": "healthy",
                "api_accessible": True,
                "model_info": {
                    "model": response.model,
                    "available": True
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e),
                "model_info": {
                    "model": self.default_model,
                    "available": False
                }
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the configured model
        
        Returns:
            Dict with model information
        """
        try:
            # Test if model is accessible by making a minimal request
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            
            return {
                "model": self.default_model,
                "available": True,
                "response_model": response.model
            }
            
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return {
                "model": self.default_model,
                "available": False,
                "error": str(e)
            }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate OpenAI service configuration
        
        Returns:
            Dict with validation results
        """
        try:
            # Check API key presence
            api_key_present = bool(config.OPENAI_API_KEY)
            
            # Check model configuration
            model_configured = bool(self.default_model)
            
            # Check model availability
            model_info = self.get_model_info()
            model_available = model_info.get("available", False)
            
            status = "valid" if (api_key_present and model_configured and model_available) else "invalid"
            
            return {
                "status": status,
                "api_key_present": api_key_present,
                "model_configured": model_configured,
                "model_available": model_available
            }
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return {
                "status": "error",
                "api_key_present": bool(config.OPENAI_API_KEY),
                "model_configured": bool(self.default_model),
                "model_available": False,
                "error": str(e)
            }
    
    def create_completion(self, messages: List[Dict[str, str]], 
                         model: Optional[str] = None,
                         temperature: Optional[float] = None,
                         max_tokens: Optional[int] = None,
                         **kwargs) -> Dict[str, Any]:
        """
        Create a chat completion using OpenAI API
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            **kwargs: Additional OpenAI API parameters
            
        Returns:
            Dict with completion response including content, model, and usage
        """
        try:
            # Validate input
            if not messages:
                raise ValueError("Messages list cannot be empty")
            
            # Validate message format
            for msg in messages:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    raise ValueError("Each message must have 'role' and 'content' keys")
                if msg['role'] not in ['system', 'user', 'assistant']:
                    raise ValueError(f"Invalid role: {msg['role']}")
            
            # Set defaults
            model = model or self.default_model
            temperature = temperature if temperature is not None else self.default_temperature
            max_tokens = max_tokens or self.default_max_tokens
            
            # Validate max_tokens
            if max_tokens > 4000:  # Reasonable limit to prevent excessive requests
                raise ValueError("max_tokens cannot exceed 4000")
            
            # Make API request
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract and return relevant information
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"Error creating completion: {e}")
            raise  # Re-raise to allow tests to catch specific errors
    
    def create_simple_completion(self, prompt: str, **kwargs) -> str:
        """
        Create a simple completion from a text prompt
        
        Args:
            prompt: Text prompt for completion
            **kwargs: Additional parameters for create_completion
            
        Returns:
            Completion text content
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.create_completion(messages=messages, **kwargs)
        return response["content"]
    
    def create_system_completion(self, system_message: str, user_message: str, **kwargs) -> str:
        """
        Create completion with system and user messages
        
        Args:
            system_message: System instruction message
            user_message: User message
            **kwargs: Additional parameters for create_completion
            
        Returns:
            Completion text content
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        response = self.create_completion(messages=messages, **kwargs)
        return response["content"]
    
    def moderate_content(self, content: str) -> Dict[str, Any]:
        """
        Moderate content using OpenAI Moderation API
        
        Args:
            content: Text content to moderate
            
        Returns:
            Dict with moderation results including safety determination
        """
        try:
            # Validate input
            if content is None:
                raise ValueError("Content cannot be None")
            
            if not isinstance(content, str):
                raise ValueError("Content must be a string")
            
            # Handle empty or whitespace-only content
            if not content.strip():
                return {
                    "flagged": False,
                    "categories": {},
                    "category_scores": {},
                    "safe": True,
                    "model": "text-moderation-stable",
                    "id": "empty-content"
                }
            
            # Call OpenAI Moderation API
            response = self.client.moderations.create(input=content)
            
            # Extract the first result (since we're sending single content)
            result = response.results[0]
            
            # Create enriched response with our custom safety determination
            moderation_result = {
                "flagged": result.flagged,
                "categories": result.categories.model_dump(),
                "category_scores": result.category_scores.model_dump(),
                "safe": not result.flagged,  # Safe if not flagged
                "model": response.model,
                "id": response.id
            }
            
            return moderation_result
            
        except Exception as e:
            logger.error(f"Error moderating content: {e}")
            raise  # Re-raise to allow tests to catch specific errors
    
    def moderate_content_strict(self, content: str, strict_threshold: float = 0.1) -> Dict[str, Any]:
        """
        Moderate content with stricter thresholds for enhanced safety
        
        Args:
            content: Text content to moderate
            strict_threshold: Lower threshold for flagging content (default 0.1)
            
        Returns:
            Dict with moderation results using stricter safety determination
        """
        # Get standard moderation result
        result = self.moderate_content(content)
        
        # Apply stricter thresholds
        category_scores = result["category_scores"]
        
        # Check if any score exceeds strict threshold (handle None values)
        strict_flagged = any(
            score is not None and score > strict_threshold 
            for score in category_scores.values()
        )
        
        # Override safety determination with strict threshold
        result["safe"] = not (result["flagged"] or strict_flagged)
        result["strict_mode"] = True
        result["strict_threshold"] = strict_threshold
        
        return result 