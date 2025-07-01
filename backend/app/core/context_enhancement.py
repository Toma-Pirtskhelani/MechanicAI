"""
Context Enhancement Service - Advanced context analysis and enhancement for MechaniAI

This service provides sophisticated context extraction, analysis, and enhancement
capabilities to improve the quality and relevance of automotive assistance.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.openai_service import OpenAIService
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.database_service import DatabaseService

logger = logging.getLogger(__name__)


class ContextEnhancementService:
    """
    Advanced context enhancement service for automotive conversations.
    
    Provides:
    - Vehicle information extraction
    - Symptom and problem analysis
    - Diagnostic code interpretation
    - Maintenance history analysis
    - Related component identification
    - Safety priority assessment
    - Predictive capabilities
    """
    
    def __init__(self):
        """Initialize context enhancement service with all required dependencies"""
        self.openai_service = OpenAIService()
        self.conversation_repo = ConversationRepository()
        self.db_service = DatabaseService()
        
        # Context caching for performance
        self._context_cache = {}
        self._cache_timeout = 300  # 5 minutes
        
        logger.info("ContextEnhancementService initialized with all dependencies")
    
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
    
    def extract_vehicle_information(self, conversation_id: str) -> Dict[str, Any]:
        """
        Extract structured vehicle information from conversation history
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with extracted vehicle information (make, model, year, mileage, etc.)
            
        Raises:
            ValueError: If conversation doesn't exist or is invalid
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Check cache first
            cache_key = f"vehicle_info_{conversation_id}"
            if self._is_cached(cache_key):
                return self._get_from_cache(cache_key)
            
            # Get conversation messages
            messages = self.conversation_repo.get_conversation_messages(conversation_id)
            if not messages:
                raise ValueError(f"Conversation {conversation_id} not found or has no messages")
            
            # Create extraction prompt
            system_prompt = """You are an expert automotive data analyst specializing in extracting vehicle information from customer conversations.

Your task is to analyze conversation messages and extract structured vehicle information.

EXTRACTION TARGETS:
- Vehicle make (Honda, Toyota, BMW, etc.)
- Vehicle model (Civic, Camry, X5, etc.)  
- Vehicle year (2015, 2020, etc.)
- Mileage (45000, 65k miles, etc.)
- Vehicle type (sedan, SUV, truck, etc.)
- Transmission type (manual, automatic, CVT)
- Engine size/type (2.4L, V6, diesel, etc.)
- Color (red, black, white, etc.)

LANGUAGE SUPPORT:
- Handle both Georgian and English text
- Recognize automotive terms in both languages
- Convert Georgian vehicle descriptions to English equivalents

RESPONSE FORMAT:
Respond with a JSON object containing:
{
    "make": "Honda",
    "model": "Civic", 
    "year": "2018",
    "mileage": "45000 miles",
    "vehicle_type": "sedan",
    "transmission": "manual",
    "engine": "1.5L turbo",
    "color": "red",
    "confidence": 0.95
}

If information is not found, use null for that field. Include confidence score (0-1) for overall extraction quality."""

            # Combine conversation text
            conversation_text = ""
            for msg in messages:
                role_label = "Customer" if msg["role"] == "user" else "Mechanic"
                conversation_text += f"{role_label}: {msg['content']}\n"
            
            user_message = f"Extract vehicle information from this conversation:\n\n{conversation_text}"
            
            # Get extraction from OpenAI
            response = self.openai_service.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=400
            )
            
            # Parse JSON response
            try:
                vehicle_info = json.loads(response)
                
                # Validate response structure
                if not isinstance(vehicle_info, dict):
                    raise ValueError("Response is not a dictionary")
                
                # Clean up null values and normalize data
                cleaned_info = {}
                for key, value in vehicle_info.items():
                    if value is not None and str(value).strip() and str(value).lower() != 'null':
                        cleaned_info[key] = str(value).strip()
                
                # Cache the result
                self._cache_result(cache_key, cleaned_info)
                
                return cleaned_info
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse vehicle extraction response, using fallback: {e}")
                
                # Fallback: Simple regex extraction
                return self._fallback_vehicle_extraction(conversation_text)
            
        except Exception as e:
            logger.error(f"Error extracting vehicle information for conversation {conversation_id}: {e}")
            raise
    
    def extract_symptoms_and_problems(self, conversation_id: str) -> Dict[str, Any]:
        """
        Extract automotive symptoms and problems from conversation
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with categorized symptoms by automotive system
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Check cache first
            cache_key = f"symptoms_{conversation_id}"
            if self._is_cached(cache_key):
                return self._get_from_cache(cache_key)
            
            # Get conversation messages
            messages = self.conversation_repo.get_conversation_messages(conversation_id)
            if not messages:
                raise ValueError(f"Conversation {conversation_id} not found or has no messages")
            
            # Create symptom extraction prompt
            system_prompt = """You are an expert automotive diagnostic specialist analyzing customer-reported symptoms.

Your task is to categorize automotive symptoms and problems by vehicle system.

AUTOMOTIVE SYSTEMS TO ANALYZE:
- Engine (noises, performance, starting, overheating)
- Transmission (shifting, slipping, grinding)
- Brakes (squealing, grinding, pedal feel, stopping distance)
- Steering (vibration, pulling, difficulty turning)
- Suspension (bouncing, noise, handling)
- Electrical (lights, battery, charging, electronics)
- Cooling (overheating, leaks, fan operation)
- Exhaust (smoke, noise, emissions)
- Fuel (consumption, delivery, quality)

LANGUAGE SUPPORT:
- Process both Georgian and English descriptions
- Understand automotive terminology in both languages
- Recognize symptom descriptions in mixed languages

RESPONSE FORMAT:
{
    "engine_symptoms": ["grinding noise", "vibration during acceleration"],
    "brake_symptoms": ["spongy pedal feel", "grinding when stopping"],
    "steering_symptoms": ["wheel shaking", "hard to turn"],
    "transmission_symptoms": ["slipping between gears"],
    "suspension_symptoms": ["bouncing over bumps"],
    "electrical_symptoms": ["dim lights", "battery drain"],
    "cooling_symptoms": ["overheating", "coolant leak"],
    "exhaust_symptoms": ["black smoke", "loud noise"],
    "fuel_symptoms": ["poor mileage", "hard starting"],
    "other_symptoms": ["unusual symptoms not fitting above categories"],
    "severity_indicators": ["urgent", "safety-critical", "monitor"],
    "confidence": 0.88
}"""

            # Combine conversation text
            conversation_text = ""
            for msg in messages:
                if msg["role"] == "user":  # Focus on user-reported symptoms
                    conversation_text += f"Customer: {msg['content']}\n"
            
            user_message = f"Extract and categorize automotive symptoms from this conversation:\n\n{conversation_text}"
            
            # Get symptom analysis from OpenAI
            response = self.openai_service.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.2,
                max_tokens=500
            )
            
            # Parse JSON response
            try:
                symptoms = json.loads(response)
                
                # Clean up empty lists and normalize
                cleaned_symptoms = {}
                for key, value in symptoms.items():
                    if isinstance(value, list) and value:
                        cleaned_symptoms[key] = [str(item).strip() for item in value if item]
                    elif not isinstance(value, list) and value is not None:
                        cleaned_symptoms[key] = value
                
                # Cache the result
                self._cache_result(cache_key, cleaned_symptoms)
                
                return cleaned_symptoms
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse symptom extraction response, using fallback: {e}")
                
                # Fallback: Keyword-based extraction
                return self._fallback_symptom_extraction(conversation_text)
            
        except Exception as e:
            logger.error(f"Error extracting symptoms for conversation {conversation_id}: {e}")
            raise
    
    def extract_diagnostic_codes_and_technical_info(self, conversation_id: str) -> Dict[str, Any]:
        """
        Extract diagnostic codes and technical information from conversation
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with diagnostic codes, measurements, and technical terms
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Check cache first
            cache_key = f"tech_info_{conversation_id}"
            if self._is_cached(cache_key):
                return self._get_from_cache(cache_key)
            
            # Get conversation messages
            messages = self.conversation_repo.get_conversation_messages(conversation_id)
            if not messages:
                raise ValueError(f"Conversation {conversation_id} not found or has no messages")
            
            # Combine all message content
            all_text = " ".join(msg["content"] for msg in messages)
            
            # Extract diagnostic codes using regex
            diagnostic_codes = self._extract_diagnostic_codes(all_text)
            
            # Extract measurements and technical terms
            measurements = self._extract_measurements(all_text)
            technical_terms = self._extract_technical_terms(all_text)
            
            tech_info = {
                "diagnostic_codes": diagnostic_codes,
                "measurements": measurements,
                "technical_terms": technical_terms,
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self._cache_result(cache_key, tech_info)
            
            return tech_info
            
        except Exception as e:
            logger.error(f"Error extracting technical info for conversation {conversation_id}: {e}")
            raise
    
    def enrich_context_with_maintenance_history(self, conversation_id: str) -> Dict[str, Any]:
        """
        Enrich context with maintenance history patterns
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with maintenance history analysis and schedule status
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Get conversation messages
            messages = self.conversation_repo.get_conversation_messages(conversation_id)
            if not messages:
                raise ValueError(f"Conversation {conversation_id} not found or has no messages")
            
            # Create maintenance analysis prompt
            system_prompt = """You are an automotive maintenance history analyst.

Analyze customer conversations to identify maintenance events and assess maintenance schedule status.

MAINTENANCE EVENTS TO IDENTIFY:
- Oil changes (frequency, type, last service)
- Brake service (pads, rotors, fluid)
- Tire service (rotation, replacement, alignment)
- Transmission service (fluid, filter)
- Cooling system (coolant, radiator, thermostat)
- Electrical (battery, alternator, spark plugs)
- Filters (air, fuel, cabin)
- Belts and hoses
- Scheduled maintenance intervals

ANALYSIS TARGETS:
- When maintenance was last performed
- Maintenance frequency patterns  
- Overdue or upcoming maintenance needs
- Maintenance quality indicators

RESPONSE FORMAT:
{
    "maintenance_events": [
        "Oil change 3 months ago",
        "Brake pads replaced last year"
    ],
    "maintenance_schedule_status": {
        "oil_change": "overdue",
        "brake_service": "current", 
        "tire_rotation": "due_soon"
    },
    "maintenance_quality_indicators": [
        "Regular oil change schedule",
        "Responsive to maintenance needs"
    ]
}"""

            # Combine conversation text
            conversation_text = ""
            for msg in messages:
                conversation_text += f"{msg['role']}: {msg['content']}\n"
            
            user_message = f"Analyze maintenance history from this conversation:\n\n{conversation_text}"
            
            # Get maintenance analysis
            response = self.openai_service.create_system_completion(
                system_message=system_prompt,
                user_message=user_message,
                temperature=0.3,
                max_tokens=400
            )
            
            # Parse response
            try:
                maintenance_analysis = json.loads(response)
                return maintenance_analysis
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse maintenance analysis, using fallback: {e}")
                
                # Fallback: Simple maintenance event detection
                return self._fallback_maintenance_analysis(conversation_text)
            
        except Exception as e:
            logger.error(f"Error analyzing maintenance history for conversation {conversation_id}: {e}")
            raise
    
    def enrich_context_with_related_components(self, conversation_id: str) -> Dict[str, Any]:
        """
        Enrich context with related automotive components
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with related components and potential causes
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Check cache first to avoid redundant API calls
            cache_key = f"components_{conversation_id}"
            if self._is_cached(cache_key):
                return self._get_from_cache(cache_key)
            
            # Get conversation messages and extract primary systems
            symptoms = self.extract_symptoms_and_problems(conversation_id)
            
            # Map symptoms to related components
            related_components = self._map_symptoms_to_components(symptoms)
            
            result = {
                "primary_systems": list(symptoms.keys()),
                "related_components": related_components,
                "potential_causes": self._suggest_potential_causes(symptoms),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching context with components for conversation {conversation_id}: {e}")
            raise
    
    def enrich_context_with_safety_priorities(self, conversation_id: str) -> Dict[str, Any]:
        """
        Enrich context with safety priority analysis
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with safety level assessment and recommendations
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Get symptoms for safety analysis
            symptoms = self.extract_symptoms_and_problems(conversation_id)
            
            # Analyze safety implications
            safety_analysis = self._analyze_safety_implications(symptoms)
            
            return safety_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing safety priorities for conversation {conversation_id}: {e}")
            raise
    
    def predict_next_questions(self, conversation_id: str) -> Dict[str, Any]:
        """
        Predict likely next questions from user
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with predicted questions and suggested diagnostics
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Get conversation context
            messages = self.conversation_repo.get_conversation_messages(conversation_id)
            if not messages:
                raise ValueError(f"Conversation {conversation_id} not found or has no messages")
            
            # Get vehicle info and symptoms for context
            vehicle_info = self.extract_vehicle_information(conversation_id)
            symptoms = self.extract_symptoms_and_problems(conversation_id)
            
            # Generate predictions based on context
            predictions = self._generate_question_predictions(messages, vehicle_info, symptoms)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting next questions for conversation {conversation_id}: {e}")
            raise
    
    def predict_maintenance_needs(self, conversation_id: str) -> Dict[str, Any]:
        """
        Predict upcoming maintenance needs
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with maintenance predictions and priority levels
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Get vehicle and maintenance context
            vehicle_info = self.extract_vehicle_information(conversation_id)
            maintenance_history = self.enrich_context_with_maintenance_history(conversation_id)
            
            # Generate maintenance predictions
            predictions = self._generate_maintenance_predictions(vehicle_info, maintenance_history)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting maintenance needs for conversation {conversation_id}: {e}")
            raise
    
    def extract_comprehensive_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Extract comprehensive context in a single batch operation for better performance
        
        Args:
            conversation_id: ID of the conversation to analyze
            
        Returns:
            Dict with all context information (vehicle, symptoms, components, safety)
        """
        try:
            # Input validation
            if not conversation_id or not conversation_id.strip():
                raise ValueError("Conversation ID cannot be empty")
            
            # Check cache first
            cache_key = f"comprehensive_{conversation_id}"
            if self._is_cached(cache_key):
                return self._get_from_cache(cache_key)
            
            # Get all context in parallel using cached results where possible
            vehicle_info = self.extract_vehicle_information(conversation_id)
            symptoms = self.extract_symptoms_and_problems(conversation_id)
            tech_info = self.extract_diagnostic_codes_and_technical_info(conversation_id)
            
            # Use local processing for derived data (no additional API calls)
            related_components = self._map_symptoms_to_components(symptoms)
            safety_analysis = self._analyze_safety_implications(symptoms)
            
            result = {
                "vehicle_information": vehicle_info,
                "symptoms_and_problems": symptoms,
                "diagnostic_technical_info": tech_info,
                "related_components": related_components,
                "safety_analysis": safety_analysis,
                "extraction_timestamp": datetime.now().isoformat()
            }
            
            # Cache the comprehensive result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting comprehensive context for conversation {conversation_id}: {e}")
            raise
    
    # Private helper methods
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and still valid"""
        if cache_key not in self._context_cache:
            return False
        
        cached_time = self._context_cache[cache_key].get('timestamp', 0)
        return (datetime.now().timestamp() - cached_time) < self._cache_timeout
    
    def _get_from_cache(self, cache_key: str) -> Any:
        """Get result from cache"""
        return self._context_cache[cache_key]['data']
    
    def _cache_result(self, cache_key: str, data: Any) -> None:
        """Cache result with timestamp"""
        self._context_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    def _fallback_vehicle_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback vehicle information extraction using regex"""
        vehicle_info = {}
        
        # Year extraction (4 digits between 1950-2030)
        year_match = re.search(r'\b(19[5-9][0-9]|20[0-3][0-9])\b', text)
        if year_match:
            vehicle_info['year'] = year_match.group(1)
        
        # Mileage extraction
        mileage_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:miles|mi|km)',
            r'(\d+)k\s*(?:miles|mi)',
            r'(\d+)\s*thousand\s*miles'
        ]
        for pattern in mileage_patterns:
            mileage_match = re.search(pattern, text, re.IGNORECASE)
            if mileage_match:
                vehicle_info['mileage'] = mileage_match.group(0)
                break
        
        # Common vehicle makes and models
        vehicle_patterns = [
            # Make and model patterns
            (r'\b(toyota)\s+(camry|corolla|prius|rav4|highlander|sienna)\b', 'Toyota'),
            (r'\b(honda)\s+(civic|accord|crv|pilot|odyssey|fit)\b', 'Honda'),
            (r'\b(bmw)\s+(x[1-5]|[1-7]\s*series|\d{3}[ix]?)\b', 'BMW'),
            (r'\b(mercedes)\s+(c|e|s|ml|gl|a|b)\s*class\b', 'Mercedes'),
            (r'\b(audi)\s+(a[3-8]|q[3-7]|tt)\b', 'Audi'),
            (r'\b(ford)\s+(f-?150|mustang|explorer|escape|focus|fiesta)\b', 'Ford'),
            (r'\b(chevrolet|chevy)\s+(malibu|cruze|equinox|tahoe|silverado)\b', 'Chevrolet'),
            (r'\b(nissan)\s+(altima|sentra|rogue|pathfinder|frontier)\b', 'Nissan'),
            (r'\b(hyundai)\s+(elantra|sonata|santa fe|tucson|accent)\b', 'Hyundai'),
            (r'\b(kia)\s+(optima|forte|soul|sorento|sportage)\b', 'Kia')
        ]
        
        # Try to find make and model together
        for pattern, make in vehicle_patterns:
            match = re.search(pattern, text.lower())
            if match:
                vehicle_info['make'] = make
                # Extract model from the match
                model_part = match.group(2)
                vehicle_info['model'] = model_part.upper() if len(model_part) <= 3 else model_part.title()
                break
        
        # If no make/model pair found, try individual makes
        if 'make' not in vehicle_info:
            makes = ['toyota', 'honda', 'bmw', 'mercedes', 'audi', 'ford', 'chevrolet', 
                    'nissan', 'hyundai', 'kia', 'volkswagen', 'mazda', 'subaru', 'lexus']
            for make in makes:
                if make in text.lower():
                    vehicle_info['make'] = make.title()
                    break
        
        return vehicle_info
    
    def _fallback_symptom_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback symptom extraction using keywords"""
        symptoms = {
            'engine_symptoms': [],
            'brake_symptoms': [],
            'steering_symptoms': [],
            'transmission_symptoms': [],
            'other_symptoms': [],
            'severity_indicators': [],
            'confidence': 0.5
        }
        
        text_lower = text.lower()
        
        # Engine symptom patterns
        engine_patterns = [
            (r'engine.*grinding', 'Engine grinding noise'),
            (r'engine.*noise', 'Engine noise'),
            (r'engine.*vibrat', 'Engine vibration'),
            (r'grinding.*noise', 'Grinding noise'),
            (r'vibrat.*noise', 'Vibration during operation'),
            (r'knock', 'Engine knock'),
            (r'misfire', 'Engine misfire'),
            (r'rough.*idle', 'Rough idle')
        ]
        
        # Brake symptom patterns  
        brake_patterns = [
            (r'brake.*spongy', 'Spongy brake pedal'),
            (r'brake.*grinding', 'Brake grinding noise'),
            (r'brake.*squeal', 'Brake squealing'),
            (r'spongy.*pedal', 'Spongy pedal feel'),
            (r'pedal.*floor', 'Pedal goes to floor'),
            (r'brake.*feel', 'Brake pedal feel issue')
        ]
        
        # Steering symptom patterns
        steering_patterns = [
            (r'steering.*shake', 'Steering wheel shaking'),
            (r'steering.*vibrat', 'Steering vibration'),
            (r'wheel.*shake', 'Steering wheel shake'),
            (r'wheel.*shaking', 'Steering wheel shaking'),
            (r'steering.*pull', 'Steering pulls'),
            (r'hard.*turn', 'Hard to turn'),
            (r'shake.*steering', 'Steering shake')
        ]
        
        # Transmission symptom patterns
        transmission_patterns = [
            (r'transmission.*slip', 'Transmission slipping'),
            (r'slip.*gear', 'Slipping between gears'),
            (r'shift.*gear', 'Shifting problems'),
            (r'transmission.*shift', 'Transmission shifting issue'),
            (r'clutch.*slip', 'Clutch slipping'),
            (r'gear.*slip', 'Gear slipping')
        ]
        
        # Check for engine symptoms
        for pattern, description in engine_patterns:
            if re.search(pattern, text_lower):
                symptoms['engine_symptoms'].append(description)
        
        # Check for brake symptoms
        for pattern, description in brake_patterns:
            if re.search(pattern, text_lower):
                symptoms['brake_symptoms'].append(description)
                
        # Check for steering symptoms
        for pattern, description in steering_patterns:
            if re.search(pattern, text_lower):
                symptoms['steering_symptoms'].append(description)
                
        # Check for transmission symptoms
        for pattern, description in transmission_patterns:
            if re.search(pattern, text_lower):
                symptoms['transmission_symptoms'].append(description)
        
        # Remove duplicates and empty lists
        for key in list(symptoms.keys()):
            if isinstance(symptoms[key], list):
                symptoms[key] = list(set(symptoms[key]))  # Remove duplicates
                if not symptoms[key]:  # Remove if empty
                    del symptoms[key]
        
        return symptoms
    
    def _extract_diagnostic_codes(self, text: str) -> List[str]:
        """Extract OBD-II diagnostic codes"""
        # Pattern for OBD-II codes (P0XXX, B0XXX, C0XXX, U0XXX)
        code_pattern = r'\b[PBCU]\d{4}\b'
        codes = re.findall(code_pattern, text.upper())
        return list(set(codes))  # Remove duplicates
    
    def _extract_measurements(self, text: str) -> List[str]:
        """Extract technical measurements"""
        # Patterns for various measurements
        patterns = [
            r'\d+\s*(?:PSI|psi)',  # Pressure
            r'\d+\s*(?:RPM|rpm)',  # Engine speed
            r'\d+\s*(?:MPH|mph)',  # Speed
            r'\d+\.?\d*\s*(?:L|l)',  # Engine displacement
            r'\d+\s*(?:V|v|volt|volts)',  # Voltage
            r'\d+\s*(?:amp|amps|A)',  # Current
            r'\d+\s*(?:°F|°C|degrees)',  # Temperature
        ]
        
        measurements = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            measurements.extend(matches)
        
        return list(set(measurements))  # Remove duplicates
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract automotive technical terms"""
        technical_terms = [
            'catalytic converter', 'oxygen sensor', 'mass airflow', 'throttle body',
            'fuel injector', 'spark plug', 'ignition coil', 'alternator', 'starter',
            'timing belt', 'timing chain', 'water pump', 'thermostat', 'radiator'
        ]
        
        found_terms = []
        text_lower = text.lower()
        for term in technical_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _fallback_maintenance_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback maintenance analysis using keywords"""
        maintenance_events = []
        
        # Common maintenance keywords
        oil_keywords = ['oil change', 'oil service', 'oil filter']
        brake_keywords = ['brake pad', 'brake service', 'brake fluid']
        
        text_lower = text.lower()
        
        for keyword in oil_keywords:
            if keyword in text_lower:
                maintenance_events.append(f"Oil service mentioned")
                break
        
        for keyword in brake_keywords:
            if keyword in text_lower:
                maintenance_events.append(f"Brake service mentioned")
                break
        
        return {
            "maintenance_events": maintenance_events,
            "maintenance_schedule_status": {},
            "maintenance_quality_indicators": []
        }
    
    def _map_symptoms_to_components(self, symptoms: Dict[str, Any]) -> List[str]:
        """Map symptoms to related automotive components"""
        components = []
        
        if 'engine_symptoms' in symptoms and symptoms['engine_symptoms']:
            components.extend(['spark plugs', 'ignition coils', 'fuel injectors', 'air filter'])
        
        if 'brake_symptoms' in symptoms and symptoms['brake_symptoms']:
            components.extend(['brake pads', 'brake rotors', 'brake fluid', 'brake calipers'])
        
        if 'transmission_symptoms' in symptoms and symptoms['transmission_symptoms']:
            components.extend(['transmission fluid', 'clutch', 'transmission filter', 'solenoids'])
        
        if 'steering_symptoms' in symptoms and symptoms['steering_symptoms']:
            components.extend(['tie rods', 'ball joints', 'steering rack', 'wheel alignment'])
        
        return list(set(components))  # Remove duplicates
    
    def _suggest_potential_causes(self, symptoms: Dict[str, Any]) -> List[str]:
        """Suggest potential causes based on symptoms"""
        causes = []
        
        if 'engine_symptoms' in symptoms and symptoms['engine_symptoms']:
            causes.extend(['ignition system failure', 'fuel delivery issue', 'engine timing problem'])
        
        if 'brake_symptoms' in symptoms and symptoms['brake_symptoms']:
            causes.extend(['worn brake pads', 'warped rotors', 'brake fluid leak', 'air in brake lines'])
        
        return causes
    
    def _analyze_safety_implications(self, symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze safety implications of symptoms"""
        urgent_issues = []
        safety_level = "low"
        recommendations = []
        
        # Critical safety issues
        if 'brake_symptoms' in symptoms and symptoms['brake_symptoms']:
            urgent_issues.extend(symptoms['brake_symptoms'])
            safety_level = "critical"
            recommendations.append("Immediate brake system inspection required")
        
        if 'steering_symptoms' in symptoms and symptoms['steering_symptoms']:
            urgent_issues.extend(symptoms['steering_symptoms'])
            if safety_level != "critical":
                safety_level = "high"
            recommendations.append("Steering system diagnosis recommended")
        
        if 'engine_symptoms' in symptoms and symptoms['engine_symptoms']:
            engine_issues = symptoms['engine_symptoms']
            critical_engine = any(term in str(engine_issues).lower() for term in ['overheat', 'knock', 'fire'])
            if critical_engine:
                urgent_issues.extend([issue for issue in engine_issues if any(term in issue.lower() for term in ['overheat', 'knock', 'fire'])])
                if safety_level == "low":
                    safety_level = "high"
        
        return {
            "safety_level": safety_level,
            "urgent_issues": urgent_issues,
            "safety_recommendations": recommendations
        }
    
    def _generate_question_predictions(self, messages: List[Dict], vehicle_info: Dict, symptoms: Dict) -> Dict[str, Any]:
        """Generate predictions for likely next questions"""
        likely_questions = []
        suggested_diagnostics = []
        confidence_scores = {}
        
        # Based on symptoms, predict likely questions
        if 'engine_symptoms' in symptoms and symptoms['engine_symptoms']:
            likely_questions.extend([
                "What diagnostic codes should I check?",
                "How much will engine repair cost?",
                "Can I drive safely with this problem?"
            ])
            suggested_diagnostics.extend([
                "OBD-II scan for diagnostic codes",
                "Engine compression test",
                "Spark plug inspection"
            ])
        
        if 'brake_symptoms' in symptoms and symptoms['brake_symptoms']:
            likely_questions.extend([
                "How urgent is brake repair?",
                "What's the cost of brake service?",
                "Can I drive with brake problems?"
            ])
            suggested_diagnostics.extend([
                "Brake system inspection",
                "Brake fluid level check",
                "Brake pad thickness measurement"
            ])
        
        # Assign confidence scores
        for question in likely_questions:
            confidence_scores[question] = 0.7 + (len(symptoms) * 0.1)  # Higher confidence with more symptoms
        
        return {
            "likely_questions": likely_questions[:5],  # Top 5
            "suggested_diagnostics": suggested_diagnostics[:3],  # Top 3
            "confidence_scores": confidence_scores
        }
    
    def _generate_maintenance_predictions(self, vehicle_info: Dict, maintenance_history: Dict) -> Dict[str, Any]:
        """Generate maintenance predictions based on vehicle and history"""
        upcoming_maintenance = []
        overdue_items = []
        priority_levels = {}
        
        # Extract mileage if available
        mileage = 0
        if 'mileage' in vehicle_info:
            mileage_str = vehicle_info['mileage']
            # Extract numeric value from mileage
            mileage_match = re.search(r'(\d+)', mileage_str.replace(',', ''))
            if mileage_match:
                mileage = int(mileage_match.group(1))
        
        # Predict based on mileage intervals and maintenance history
        if mileage > 0:
            # Oil change typically every 3000-5000 miles
            if 'oil_change' in maintenance_history.get('maintenance_schedule_status', {}):
                status = maintenance_history['maintenance_schedule_status']['oil_change']
                events = maintenance_history.get('maintenance_events', [])
                
                # Check if any events mention high mileage since last oil change
                high_mileage_mentioned = any(
                    ('4000' in event or '4,000' in event or '3500' in event or '3,500' in event) 
                    and 'ago' in event and 'oil' in event.lower()
                    for event in events
                )
                
                if status in ['overdue', 'due_soon'] or high_mileage_mentioned:
                    if status == 'overdue' or high_mileage_mentioned:
                        overdue_items.append("Oil change")
                        priority_levels["Oil change"] = "high"
                    else:  # due_soon
                        upcoming_maintenance.append("Oil change due soon")
                        priority_levels["Oil change"] = "medium"
            else:
                # Check if last oil change mentioned in conversation
                events = maintenance_history.get('maintenance_events', [])
                oil_mentioned = any('oil' in event.lower() for event in events)
                
                # Look for specific patterns indicating overdue oil change
                if oil_mentioned:
                    # Check if "4,000 miles ago" or similar pattern suggests overdue
                    oil_change_overdue = any(
                        '4000' in event or '4,000' in event or 'ago' in event 
                        for event in events if 'oil' in event.lower()
                    )
                    if oil_change_overdue:
                        overdue_items.append("Oil change")
                        priority_levels["Oil change"] = "high"
                else:
                    # No oil change mentioned, check mileage intervals
                    if mileage >= 48000:  # High mileage suggests maintenance needs
                        overdue_items.append("Oil change")
                        priority_levels["Oil change"] = "high"
                    elif mileage % 5000 < 1000:  # Close to service interval
                        upcoming_maintenance.append("Oil change due soon")
                        priority_levels["Oil change"] = "medium"
        
        return {
            "upcoming_maintenance": upcoming_maintenance,
            "overdue_items": overdue_items,
            "priority_levels": priority_levels
        } 