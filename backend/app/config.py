import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration management class for MechaniAI"""
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Supabase
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    
    # App Config
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def validate_required_env_vars(cls) -> dict[str, str]:
        """Validate that all required environment variables are set"""
        missing_vars = []
        
        if not cls.OPENAI_API_KEY:
            missing_vars.append("OPENAI_API_KEY")
        if not cls.SUPABASE_URL:
            missing_vars.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing_vars.append("SUPABASE_KEY")
            
        if missing_vars:
            return {"status": "error", "missing_vars": missing_vars}
        
        return {"status": "ok", "message": "All required environment variables are set"}


# Global config instance
config = Config() 