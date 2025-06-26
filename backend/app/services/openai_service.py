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
    
    def check_automotive_relevance(self, query: str) -> Dict[str, Any]:
        """
        Check if a user query is related to automotive/vehicle mechanics and repair
        
        Args:
            query: User query to analyze for automotive relevance
            
        Returns:
            Dict with automotive relevance analysis including:
            - is_automotive: Boolean indicating if query is automotive-related
            - confidence: Float between 0-1 indicating confidence level
            - reasoning: String explanation of the determination
        """
        try:
            # Validate input
            if query is None:
                raise ValueError("Query cannot be None")
            
            if not isinstance(query, str):
                raise ValueError("Query must be a string")
            
            # Handle empty or very short queries
            if not query.strip() or len(query.strip()) < 2:
                return {
                    "is_automotive": False,
                    "confidence": 1.0,
                    "reasoning": "Query is empty or too short to be meaningful automotive content"
                }
            
            # Create system prompt for automotive relevance detection
            system_prompt = """You are an expert automotive mechanic and consultant for Tegeta Motors.

Your task is to determine if a user query is related to automotive mechanics, vehicle repair, diagnostics, or maintenance.

AUTOMOTIVE TOPICS INCLUDE:
- Engine problems, repairs, diagnostics
- Transmission, brake, suspension issues
- Electrical system problems
- Oil changes, fluid maintenance
- Vehicle diagnostic codes (OBD-II)
- Parts replacement and repair procedures
- Any mechanical or electrical vehicle issues
- Motorcycle, truck, or other vehicle mechanics

NON-AUTOMOTIVE TOPICS INCLUDE:
- Car insurance, financing, sales
- Car wash services
- Traffic laws and regulations
- Driving lessons or tips
- General automotive news or reviews
- Non-mechanical car-related services

LANGUAGE SUPPORT:
- Handle both Georgian and English queries equally
- Mixed language queries are acceptable
- Technical automotive terms in either language

RESPONSE FORMAT:
Respond with a JSON object containing:
{
    "is_automotive": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your determination"
}

Be precise and conservative. When in doubt about borderline cases, lean towards marking as non-automotive unless there's clear mechanical/repair intent."""

            # Create user message
            user_message = f"Analyze this query for automotive relevance: \"{query}\""
            
            # Get response from OpenAI
            response = self.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=200    # Reasonable limit for structured response
            )
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response)
                
                # Validate response structure
                if not isinstance(result, dict):
                    raise ValueError("Response is not a dictionary")
                
                required_keys = ["is_automotive", "confidence", "reasoning"]
                for key in required_keys:
                    if key not in result:
                        raise ValueError(f"Missing required key: {key}")
                
                # Validate data types and ranges
                if not isinstance(result["is_automotive"], bool):
                    raise ValueError("is_automotive must be boolean")
                
                if not isinstance(result["confidence"], (int, float)):
                    raise ValueError("confidence must be numeric")
                
                if not (0 <= result["confidence"] <= 1):
                    raise ValueError("confidence must be between 0 and 1")
                
                if not isinstance(result["reasoning"], str):
                    raise ValueError("reasoning must be string")
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback: Parse response manually if JSON parsing fails
                logger.warning(f"Failed to parse JSON response, using fallback analysis: {e}")
                
                # Simple keyword-based fallback
                automotive_keywords = [
                    # English keywords
                    'engine', 'brake', 'transmission', 'oil', 'car', 'vehicle', 'motor',
                    'repair', 'fix', 'diagnostic', 'battery', 'tire', 'wheel', 'exhaust',
                    'suspension', 'clutch', 'radiator', 'alternator', 'starter',
                    # Georgian keywords
                    'მანქანა', 'ძრავა', 'სამუხრუჭე', 'ზეთი', 'გადაცემათა', 'კოლოფი',
                    'რემონტი', 'გაწკდომა', 'ბატარეა', 'საბურავი', 'ბორბალი'
                ]
                
                query_lower = query.lower()
                automotive_matches = sum(1 for keyword in automotive_keywords if keyword in query_lower)
                
                if automotive_matches > 0:
                    confidence = min(0.8, automotive_matches * 0.3)
                    return {
                        "is_automotive": True,
                        "confidence": confidence,
                        "reasoning": f"Detected automotive keywords (fallback analysis). Found {automotive_matches} relevant terms."
                    }
                else:
                    return {
                        "is_automotive": False,
                        "confidence": 0.6,
                        "reasoning": "No clear automotive keywords detected (fallback analysis)"
                    }
            
        except Exception as e:
            logger.error(f"Error checking automotive relevance: {e}")
            raise  # Re-raise to allow tests to catch specific errors
    
    def generate_expert_response(self, query: str, context: Optional[Dict[str, Any]] = None, 
                               conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Generate expert automotive advice for user queries
        
        Args:
            query: User query requiring expert automotive advice
            context: Optional context about vehicle (make, model, year, mileage, etc.)
            conversation_history: Optional previous conversation messages
            
        Returns:
            Dict with expert response including:
            - response: Expert automotive advice text
            - confidence: Float between 0-1 indicating confidence level  
            - language: Detected language ("en", "ka", or "mixed")
        """
        try:
            # Validate input
            if query is None:
                raise ValueError("Query cannot be None")
            
            if not isinstance(query, str):
                raise ValueError("Query must be a string")
            
            # Handle empty or very short queries
            if not query.strip():
                return {
                    "response": "I'm here to help with automotive questions. Please describe the issue you're experiencing with your vehicle, and I'll provide professional advice.",
                    "confidence": 0.8,
                    "language": "en"
                }
            
            # Detect language
            detected_language = self._detect_query_language(query)
            
            # Create expert system prompt
            system_prompt = self._create_expert_system_prompt(detected_language)
            
            # Build message context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                        messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add vehicle context if provided
            context_info = ""
            if context:
                context_parts = []
                if context.get("vehicle_make"):
                    context_parts.append(f"Make: {context['vehicle_make']}")
                if context.get("vehicle_model"):
                    context_parts.append(f"Model: {context['vehicle_model']}")
                if context.get("vehicle_year"):
                    context_parts.append(f"Year: {context['vehicle_year']}")
                if context.get("mileage"):
                    context_parts.append(f"Mileage: {context['mileage']}")
                
                if context_parts:
                    context_info = f"Vehicle Information: {', '.join(context_parts)}\n\n"
            
            # Create the user message with context
            user_message = f"{context_info}Customer Question: {query}"
            messages.append({"role": "user", "content": user_message})
            
            # Generate expert response
            response = self.create_completion(
                messages=messages,
                temperature=0.3,  # Low temperature for consistent, professional advice
                max_tokens=800    # Allow for detailed responses
            )
            
            expert_response = response["content"]
            
            # Calculate confidence based on response quality
            confidence = self._calculate_response_confidence(query, expert_response, detected_language)
            
            return {
                "response": expert_response,
                "confidence": confidence,
                "language": detected_language
            }
            
        except Exception as e:
            logger.error(f"Error generating expert response: {e}")
            raise  # Re-raise to allow tests to catch specific errors
    
    def _detect_query_language(self, query: str) -> str:
        """
        Detect the primary language of the query
        
        Args:
            query: Input query text
            
        Returns:
            Language code: "en", "ka", or "mixed"
        """
        # Georgian Unicode range check
        georgian_chars = sum(1 for char in query if '\u10A0' <= char <= '\u10FF')
        english_chars = sum(1 for char in query if char.isalpha() and char.isascii())
        
        total_chars = georgian_chars + english_chars
        
        if total_chars == 0:
            return "en"  # Default to English for non-alphabetic queries
        
        georgian_ratio = georgian_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if georgian_ratio > 0.6:
            return "ka"
        elif english_ratio > 0.6:
            return "en"
        else:
            return "mixed"
    
    def _create_expert_system_prompt(self, language: str) -> str:
        """
        Create expert system prompt based on detected language
        
        Args:
            language: Detected language code
            
        Returns:
            System prompt for expert automotive advice
        """
        base_prompt = """You are an expert automotive technician and mechanic working for Tegeta Motors, a premier automotive service provider in Georgia.

EXPERTISE AREAS:
- Engine diagnostics and repair (all types: gasoline, diesel, hybrid)
- Transmission systems (manual, automatic, CVT)
- Brake systems (hydraulic, electric, ABS, ESP)
- Electrical systems (starting, charging, ECU, sensors)
- Cooling and heating systems
- Suspension and steering systems
- Fuel systems and emissions control
- Diagnostic trouble codes (OBD-II)
- Preventive maintenance schedules

PROFESSIONAL STANDARDS:
- Provide accurate, helpful automotive advice
- Use clear explanations for technical concepts
- Always prioritize safety in recommendations
- Suggest professional inspection for complex issues
- Give specific diagnostic steps when appropriate
- Include cost considerations when relevant
- Recommend genuine or quality aftermarket parts

SAFETY PROTOCOLS:
- Immediately flag dangerous situations (brake failure, steering issues, overheating)
- Recommend stopping driving when safety is compromised
- Advise seeking immediate professional help for critical issues
- Include proper safety precautions for DIY work

COMMUNICATION STYLE:
- Professional yet friendly and approachable
- Patient with customers of all knowledge levels
- Avoid unnecessary technical jargon
- Explain automotive concepts in understandable terms
- Provide step-by-step guidance when appropriate"""

        if language == "ka":
            return base_prompt + """

LANGUAGE INSTRUCTIONS:
- Respond primarily in Georgian when the customer writes in Georgian
- Use automotive terminology that Georgian customers understand
- You may include English technical terms in parentheses when helpful
- Be culturally appropriate for Georgian automotive service standards"""

        elif language == "mixed":
            return base_prompt + """

LANGUAGE INSTRUCTIONS:
- Respond in the language that seems most comfortable for the customer
- Georgian and English mixed queries should be answered helpfully
- Use both languages as needed for clarity
- Include technical terms in both languages when helpful"""

        else:  # English
            return base_prompt + """

LANGUAGE INSTRUCTIONS:
- Respond in clear, professional English
- Use automotive terminology appropriately
- Explain technical terms when necessary
- Maintain international automotive service standards"""
    
    def _calculate_response_confidence(self, query: str, response: str, language: str) -> float:
        """
        Calculate confidence score for the expert response
        
        Args:
            query: Original user query
            response: Generated expert response
            language: Detected language
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.7  # Base confidence
        
        # Adjust based on response length (more detailed = higher confidence)
        if len(response) > 200:
            confidence += 0.1
        elif len(response) > 100:
            confidence += 0.05
        elif len(response) < 50:
            confidence -= 0.2
        
        # Check for automotive terminology
        automotive_terms = [
            "engine", "brake", "transmission", "oil", "fuel", "battery", "alternator",
            "starter", "radiator", "coolant", "tire", "suspension", "diagnostic",
            "მანქანა", "ძრავა", "სამუხრუჭე", "ზეთი", "ბატარეა", "გადაცემათა"
        ]
        
        response_lower = response.lower()
        found_terms = sum(1 for term in automotive_terms if term in response_lower)
        
        if found_terms >= 3:
            confidence += 0.1
        elif found_terms >= 2:
            confidence += 0.05
        elif found_terms == 0:
            confidence -= 0.3
        
        # Check for safety considerations
        safety_terms = ["safety", "danger", "immediately", "professional", "mechanic", "safe"]
        found_safety = sum(1 for term in safety_terms if term in response_lower)
        
        if found_safety >= 2:
            confidence += 0.05
        
        # Language consistency bonus
        if language == "ka" and any(char for char in response if '\u10A0' <= char <= '\u10FF'):
            confidence += 0.05
        elif language == "en" and not any(char for char in response if '\u10A0' <= char <= '\u10FF'):
            confidence += 0.05
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))
    
    def compress_conversation_context(self, conversation_messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Compress conversation history while preserving essential information
        
        Args:
            conversation_messages: List of conversation messages with 'role' and 'content'
            
        Returns:
            Dict with compression results including:
            - compressed_context: Summarized conversation text
            - compression_ratio: Float indicating compression achieved (0-1)
            - preserved_information: Dict with preserved critical information
        """
        try:
            # Validate input
            if conversation_messages is None:
                raise ValueError("Conversation messages cannot be None")
            
            if not isinstance(conversation_messages, list):
                raise ValueError("Conversation messages must be a list")
            
            # Handle empty conversation
            if len(conversation_messages) == 0:
                return {
                    "compressed_context": "",
                    "compression_ratio": 1.0,
                    "preserved_information": {
                        "topics": [],
                        "vehicle_info": {},
                        "safety_flags": []
                    }
                }
            
            # Filter valid messages
            valid_messages = []
            for msg in conversation_messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] in ["user", "assistant", "system"] and msg["content"].strip():
                        valid_messages.append(msg)
            
            # Handle minimal conversations
            if len(valid_messages) <= 2:
                original_text = " ".join(msg["content"] for msg in valid_messages)
                return {
                    "compressed_context": original_text,
                    "compression_ratio": 1.0,
                    "preserved_information": self._extract_preserved_information(valid_messages)
                }
            
            # Create compression system prompt
            system_prompt = """You are an expert at summarizing automotive technical conversations while preserving all critical information.

COMPRESSION OBJECTIVES:
- Preserve all automotive technical details (parts, symptoms, diagnostics)
- Maintain vehicle information (make, model, year, mileage)
- Keep all diagnostic codes (P-codes, error codes)
- Preserve safety warnings and urgent recommendations
- Maintain the logical flow of diagnosis and advice
- Keep customer's specific problems and mechanic's solutions

CRITICAL PRESERVATION REQUIREMENTS:
- Vehicle specifications (make, model, year, mileage)
- Specific symptoms (noises, behaviors, timing)
- Diagnostic codes and technical terms
- Safety concerns and warnings
- Repair recommendations and next steps
- Parts mentioned (brake pads, oil, filters, etc.)
- Maintenance schedules and intervals

COMPRESSION GUIDELINES:
- Remove conversational fluff ("Hello", "Thank you", "You're welcome")
- Combine similar exchanges about the same topic
- Use technical shorthand where appropriate
- Maintain chronological order of issues discussed
- Preserve exact technical terms and code numbers

OUTPUT FORMAT:
Provide a concise technical summary that preserves all essential automotive information while removing unnecessary conversational elements. Focus on the technical content and actionable advice."""

            # Convert conversation to text for compression
            conversation_text = ""
            for msg in valid_messages:
                role_label = "Customer" if msg["role"] == "user" else "Mechanic"
                conversation_text += f"{role_label}: {msg['content']}\n"
            
            # Create compression request
            user_message = f"Compress this automotive conversation while preserving all technical details:\n\n{conversation_text}"
            
            # Generate compressed context
            response = self.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.2,  # Low temperature for consistent compression
                max_tokens=600    # Allow for detailed preservation
            )
            
            compressed_context = response.strip()
            
            # Calculate compression ratio
            original_length = len(conversation_text)
            compressed_length = len(compressed_context)
            compression_ratio = compressed_length / original_length if original_length > 0 else 1.0
            
            # Extract preserved information
            preserved_info = self._extract_preserved_information(valid_messages)
            
            return {
                "compressed_context": compressed_context,
                "compression_ratio": compression_ratio,
                "preserved_information": preserved_info
            }
            
        except Exception as e:
            logger.error(f"Error compressing conversation context: {e}")
            raise  # Re-raise to allow tests to catch specific errors
    
    def _extract_preserved_information(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract and categorize preserved information from conversation
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dict with categorized preserved information
        """
        preserved_info = {
            "topics": [],
            "vehicle_info": {},
            "safety_flags": []
        }
        
        # Combine all message content for analysis
        all_text = " ".join(msg["content"].lower() for msg in messages)
        
        # Extract automotive topics
        automotive_topics = {
            "engine": ["engine", "motor", "piston", "cylinder", "timing", "valve"],
            "brakes": ["brake", "pad", "disc", "rotor", "pedal", "stopping"],
            "transmission": ["transmission", "gear", "shift", "clutch", "automatic", "manual"],
            "electrical": ["battery", "alternator", "starter", "ignition", "electrical", "wire"],
            "cooling": ["coolant", "radiator", "thermostat", "overheat", "fan", "temperature"],
            "fuel": ["fuel", "gas", "diesel", "injection", "pump", "filter"],
            "suspension": ["suspension", "shock", "strut", "spring", "wheel", "tire"],
            "exhaust": ["exhaust", "muffler", "catalytic", "converter", "emission"]
        }
        
        for topic, keywords in automotive_topics.items():
            if any(keyword in all_text for keyword in keywords):
                preserved_info["topics"].append(topic)
        
        # Extract vehicle information
        import re
        
        # Year patterns (4 digits between 1950-2030)
        years = re.findall(r'\b(19[5-9][0-9]|20[0-3][0-9])\b', all_text)
        if years:
            preserved_info["vehicle_info"]["year"] = years[0]
        
        # Mileage patterns
        mileage_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:miles|mi|km)',
            r'(\d+)k\s*(?:miles|mi)',
            r'(\d+)\s*thousand\s*miles'
        ]
        for pattern in mileage_patterns:
            mileage_match = re.search(pattern, all_text)
            if mileage_match:
                preserved_info["vehicle_info"]["mileage"] = mileage_match.group(1)
                break
        
        # Common vehicle makes
        vehicle_makes = ["toyota", "honda", "bmw", "mercedes", "audi", "ford", "chevrolet", 
                        "nissan", "hyundai", "kia", "volkswagen", "mazda", "subaru", "lexus"]
        for make in vehicle_makes:
            if make in all_text:
                preserved_info["vehicle_info"]["make"] = make.title()
                break
        
        # Safety flag detection
        safety_keywords = [
            "dangerous", "safety", "immediately", "stop driving", "do not drive",
            "emergency", "urgent", "critical", "brake failure", "steering",
            "life threatening", "pull over", "towing", "unsafe"
        ]
        
        for keyword in safety_keywords:
            if keyword in all_text:
                preserved_info["safety_flags"].append(keyword)
        
        # Remove duplicates and limit length
        preserved_info["topics"] = list(set(preserved_info["topics"]))[:5]
        preserved_info["safety_flags"] = list(set(preserved_info["safety_flags"]))[:3]
        
        return preserved_info

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the primary language of input text with confidence scoring
        
        Args:
            text: Input text to analyze for language
            
        Returns:
            Dict with language detection results including:
            - language: Language code ("en", "ka", or "mixed")
            - confidence: Float between 0-1 indicating confidence level
            - reasoning: String explanation of the determination
        """
        try:
            # Validate input
            if text is None:
                raise ValueError("Text cannot be None")
            
            if not isinstance(text, str):
                raise ValueError("Text must be a string")
            
            # Handle empty or very short text
            if not text.strip():
                return {
                    "language": "en",
                    "confidence": 0.9,
                    "reasoning": "Empty text defaults to English"
                }
            
            if len(text.strip()) < 3:
                return {
                    "language": "en",
                    "confidence": 0.7,
                    "reasoning": "Very short text defaults to English"
                }
            
            # Use existing language detection logic with enhanced response
            detected_lang = self._detect_query_language(text)
            
            # Calculate confidence based on character analysis
            georgian_chars = sum(1 for char in text if '\u10A0' <= char <= '\u10FF')
            english_chars = sum(1 for char in text if char.isalpha() and char.isascii())
            total_chars = georgian_chars + english_chars
            
            if total_chars == 0:
                return {
                    "language": "en",
                    "confidence": 0.6,
                    "reasoning": "No alphabetic characters detected, defaulting to English"
                }
            
            georgian_ratio = georgian_chars / total_chars
            english_ratio = english_chars / total_chars
            
            # Enhanced confidence calculation
            if detected_lang == "ka":
                confidence = 0.7 + (georgian_ratio * 0.3)
                reasoning = f"Georgian detected ({georgian_ratio:.1%} Georgian characters)"
            elif detected_lang == "en":
                confidence = 0.7 + (english_ratio * 0.3)
                reasoning = f"English detected ({english_ratio:.1%} English characters)"
            else:  # mixed
                confidence = 0.5 + (min(georgian_ratio, english_ratio) * 0.4)
                reasoning = f"Mixed language detected (Georgian: {georgian_ratio:.1%}, English: {english_ratio:.1%})"
            
            return {
                "language": detected_lang,
                "confidence": min(1.0, confidence),
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            raise  # Re-raise to allow tests to catch specific errors

    def translate_to_georgian(self, text: str) -> Dict[str, Any]:
        """
        Translate English text to Georgian with automotive context preservation
        
        Args:
            text: English text to translate to Georgian
            
        Returns:
            Dict with translation results including:
            - translated_text: Georgian translation
            - confidence: Float between 0-1 indicating translation confidence
            - original_language: Detected original language
        """
        try:
            # Validate input
            if text is None:
                raise ValueError("Text cannot be None")
            
            if not isinstance(text, str):
                raise ValueError("Text must be a string")
            
            # Handle empty text
            if not text.strip():
                return {
                    "translated_text": "",
                    "confidence": 1.0,
                    "original_language": "en"
                }
            
            # Detect original language
            lang_detection = self.detect_language(text)
            original_lang = lang_detection["language"]
            
            # If already Georgian, return as-is
            if original_lang == "ka":
                return {
                    "translated_text": text,
                    "confidence": 0.95,
                    "original_language": "ka"
                }
            
            # Create translation system prompt
            system_prompt = """You are an expert automotive translator specializing in English to Georgian translation.

TRANSLATION REQUIREMENTS:
- Translate automotive technical content accurately into Georgian
- Preserve all technical codes (P-codes, OBD-II codes) exactly as written
- Preserve all measurements and numbers (keep original units or convert appropriately)
- Maintain automotive terminology precision
- Use standard Georgian automotive vocabulary
- Preserve the professional tone and technical accuracy

TECHNICAL PRESERVATION:
- Diagnostic codes like P0301, OBD-II should remain unchanged
- Part names should be translated but keep recognizable technical terms
- Safety warnings must be accurately conveyed
- Measurements can be kept in original units or converted (mm, inches, etc.)

AUTOMOTIVE VOCABULARY:
- Engine = ძრავა
- Brake = სამუხრუჭე
- Transmission = გადაცემათა კოლოფი
- Battery = ბატარეა
- Oil = ზეთი
- Coolant = გამაგრილებელი სითხე
- Radiator = რადიატორი
- Alternator = გენერატორი
- Starter = სტარტერი

OUTPUT: Provide only the Georgian translation, maintaining technical accuracy and professional tone."""

            # Create user message
            user_message = f"Translate this automotive text to Georgian: \"{text}\""
            
            # Generate translation
            response = self.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.2,  # Low temperature for consistent translation
                max_tokens=600    # Allow for detailed translations
            )
            
            translated_text = response.strip()
            
            # Calculate translation confidence
            confidence = self._calculate_translation_confidence(text, translated_text, "en", "ka")
            
            return {
                "translated_text": translated_text,
                "confidence": confidence,
                "original_language": original_lang
            }
            
        except Exception as e:
            logger.error(f"Error translating to Georgian: {e}")
            raise  # Re-raise to allow tests to catch specific errors

    def translate_to_english(self, text: str) -> Dict[str, Any]:
        """
        Translate Georgian text to English with automotive context preservation
        
        Args:
            text: Georgian text to translate to English
            
        Returns:
            Dict with translation results including:
            - translated_text: English translation
            - confidence: Float between 0-1 indicating translation confidence
            - original_language: Detected original language
        """
        try:
            # Validate input
            if text is None:
                raise ValueError("Text cannot be None")
            
            if not isinstance(text, str):
                raise ValueError("Text must be a string")
            
            # Handle empty text
            if not text.strip():
                return {
                    "translated_text": "",
                    "confidence": 1.0,
                    "original_language": "ka"
                }
            
            # Detect original language
            lang_detection = self.detect_language(text)
            original_lang = lang_detection["language"]
            
            # If already English, return as-is
            if original_lang == "en":
                return {
                    "translated_text": text,
                    "confidence": 0.95,
                    "original_language": "en"
                }
            
            # Create translation system prompt
            system_prompt = """You are an expert automotive translator specializing in Georgian to English translation.

TRANSLATION REQUIREMENTS:
- Translate automotive technical content accurately into English
- Preserve all technical codes (P-codes, OBD-II codes) exactly as written
- Preserve all measurements and numbers with appropriate unit conversions
- Maintain automotive terminology precision
- Use standard English automotive vocabulary
- Preserve the professional tone and technical accuracy

TECHNICAL PRESERVATION:
- Diagnostic codes like P0301, OBD-II should remain unchanged
- Georgian automotive terms should be translated to standard English equivalents
- Safety warnings must be accurately conveyed
- Measurements should use appropriate English units (inches, feet, gallons, etc.)

AUTOMOTIVE VOCABULARY REFERENCE:
- ძრავა = Engine
- სამუხრუჭე = Brake
- გადაცემათა კოლოფი = Transmission
- ბატარეა = Battery
- ზეთი = Oil
- გამაგრილებელი სითხე = Coolant
- რადიატორი = Radiator
- გენერატორი = Alternator
- სტარტერი = Starter

OUTPUT: Provide only the English translation, maintaining technical accuracy and professional tone."""

            # Create user message
            user_message = f"Translate this automotive text to English: \"{text}\""
            
            # Generate translation
            response = self.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.2,  # Low temperature for consistent translation
                max_tokens=600    # Allow for detailed translations
            )
            
            translated_text = response.strip()
            
            # Calculate translation confidence
            confidence = self._calculate_translation_confidence(text, translated_text, original_lang, "en")
            
            return {
                "translated_text": translated_text,
                "confidence": confidence,
                "original_language": original_lang
            }
            
        except Exception as e:
            logger.error(f"Error translating to English: {e}")
            raise  # Re-raise to allow tests to catch specific errors

    def auto_translate_response(self, user_query: str, system_response: str) -> Dict[str, Any]:
        """
        Automatically translate system response to match user's language preference
        
        Args:
            user_query: Original user query to detect language preference
            system_response: System response that may need translation
            
        Returns:
            Dict with auto-translation results including:
            - needs_translation: Boolean indicating if translation was needed
            - user_language: Detected user language preference
            - response_language: Detected system response language
            - translated_response: Translated response (or original if no translation needed)
            - confidence: Float between 0-1 indicating translation confidence
        """
        try:
            # Validate input
            if user_query is None or system_response is None:
                raise ValueError("Both user_query and system_response cannot be None")
            
            if not isinstance(user_query, str) or not isinstance(system_response, str):
                raise ValueError("Both user_query and system_response must be strings")
            
            # Detect languages
            user_lang_detection = self.detect_language(user_query)
            response_lang_detection = self.detect_language(system_response)
            
            user_language = user_lang_detection["language"]
            response_language = response_lang_detection["language"]
            
            # Determine if translation is needed
            needs_translation = False
            translated_response = system_response
            confidence = 0.95  # High confidence for no translation
            
            # Translation logic
            if user_language == "en" and response_language == "ka":
                # User speaks English, response is Georgian -> translate to English
                translation_result = self.translate_to_english(system_response)
                translated_response = translation_result["translated_text"]
                confidence = translation_result["confidence"]
                needs_translation = True
                
            elif user_language == "ka" and response_language == "en":
                # User speaks Georgian, response is English -> translate to Georgian
                translation_result = self.translate_to_georgian(system_response)
                translated_response = translation_result["translated_text"]
                confidence = translation_result["confidence"]
                needs_translation = True
                
            elif user_language == "mixed":
                # Mixed language user - keep response as-is for now
                # Future enhancement: Could implement smart language selection
                needs_translation = False
                confidence = 0.8
                
            else:
                # Languages match or no translation needed
                needs_translation = False
                confidence = 0.9
            
            return {
                "needs_translation": needs_translation,
                "user_language": user_language,
                "response_language": response_language,
                "translated_response": translated_response,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error in auto-translate response: {e}")
            raise  # Re-raise to allow tests to catch specific errors

    def _calculate_translation_confidence(self, original_text: str, translated_text: str, 
                                        source_lang: str, target_lang: str) -> float:
        """
        Calculate confidence score for translation quality
        
        Args:
            original_text: Original text before translation
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.7  # Base confidence
        
        # Check if translation actually occurred (different from original)
        if original_text.strip() == translated_text.strip():
            if source_lang == target_lang:
                confidence = 0.95  # Same language, no translation needed
            else:
                confidence = 0.3   # No translation when expected
        
        # Check for appropriate target language characters
        if target_lang == "ka":
            georgian_chars = sum(1 for char in translated_text if '\u10A0' <= char <= '\u10FF')
            if georgian_chars > 0:
                confidence += 0.2
            else:
                confidence -= 0.3  # Expected Georgian but didn't get it
                
        elif target_lang == "en":
            english_chars = sum(1 for char in translated_text if char.isalpha() and char.isascii())
            total_alpha = sum(1 for char in translated_text if char.isalpha())
            if total_alpha > 0 and english_chars / total_alpha > 0.7:
                confidence += 0.2
            else:
                confidence -= 0.3  # Expected English but didn't get it
        
        # Check for preserved technical codes
        import re
        codes = re.findall(r'\b[A-Z]\d{4}\b', original_text)  # P0301, U0101, etc.
        preserved_codes = sum(1 for code in codes if code in translated_text)
        if codes:
            preservation_ratio = preserved_codes / len(codes)
            confidence += preservation_ratio * 0.1
        
        # Check for reasonable length ratio
        if len(original_text) > 0:
            length_ratio = len(translated_text) / len(original_text)
            if 0.5 <= length_ratio <= 2.0:  # Reasonable translation length
                confidence += 0.05
            else:
                confidence -= 0.1  # Suspicious length ratio
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))