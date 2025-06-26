import os
import pytest
import tempfile
from app.config import Config
from supabase import create_client


class TestConfigurationComprehensive:
    """Comprehensive tests for configuration management"""
    
    def test_real_openai_credentials_validation(self):
        """Test that OpenAI credentials actually work with the API"""
        from openai import OpenAI
        
        # Test that we can create a client with our credentials
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # This is a real API call - tests actual credential validity
        try:
            # Use a very cheap API call to validate credentials
            models = client.models.list()
            assert models is not None
            # Should have at least some models available
            assert len(models.data) > 0
            # Should include GPT models
            model_ids = [model.id for model in models.data]
            assert any("gpt" in model_id.lower() for model_id in model_ids)
        except Exception as e:
            pytest.fail(f"OpenAI credentials invalid or API unreachable: {e}")
    
    def test_real_supabase_credentials_validation(self):
        """Test that Supabase credentials actually work with the API"""
        # Test that we can create a client with our credentials
        try:
            client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            
            # Perform a real operation to validate credentials
            result = client.table('conversations').select("count", count="exact").limit(0).execute()
            
            # Should get a response (even if count is 0)
            assert hasattr(result, 'count')
            assert result.count is not None
            assert result.count >= 0
            
        except Exception as e:
            pytest.fail(f"Supabase credentials invalid or API unreachable: {e}")
    
    def test_env_local_precedence(self):
        """Test that .env.local takes precedence over .env"""
        # Create temporary env files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
            temp_env.write("TEST_VALUE=from_env\n")
            temp_env_path = temp_env.name
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.local', delete=False) as temp_env_local:
            temp_env_local.write("TEST_VALUE=from_env_local\n")
            temp_env_local_path = temp_env_local.name
        
        try:
            # Clear any existing value
            if 'TEST_VALUE' in os.environ:
                del os.environ['TEST_VALUE']
            
            # Load both files (simulating our config loading)
            from dotenv import load_dotenv
            load_dotenv(temp_env_local_path)  # Load .env.local first
            load_dotenv(temp_env_path)        # Load .env second
            
            # .env.local should take precedence
            assert os.getenv('TEST_VALUE') == 'from_env_local'
            
        finally:
            # Cleanup
            os.unlink(temp_env_path)
            os.unlink(temp_env_local_path)
            if 'TEST_VALUE' in os.environ:
                del os.environ['TEST_VALUE']
    
    def test_required_vs_optional_variables(self):
        """Test validation of required vs optional environment variables"""
        # Test that all required variables are properly identified
        validation_result = Config.validate_required_env_vars()
        
        if validation_result["status"] == "error":
            pytest.fail(f"Required environment variables missing: {validation_result['missing_vars']}")
        
        # Test individual requirements
        assert Config.OPENAI_API_KEY is not None, "OPENAI_API_KEY is required"
        assert Config.OPENAI_API_KEY.startswith("sk-"), "OPENAI_API_KEY should start with 'sk-'"
        assert len(Config.OPENAI_API_KEY) > 20, "OPENAI_API_KEY seems too short"
        
        assert Config.SUPABASE_URL is not None, "SUPABASE_URL is required"
        assert Config.SUPABASE_URL.startswith("https://"), "SUPABASE_URL should start with 'https://'"
        assert ".supabase.co" in Config.SUPABASE_URL, "SUPABASE_URL should contain '.supabase.co'"
        
        assert Config.SUPABASE_KEY is not None, "SUPABASE_KEY is required"
        assert len(Config.SUPABASE_KEY) > 50, "SUPABASE_KEY seems too short"
        
        # Test optional variables have sensible defaults
        assert Config.OPENAI_MODEL == "gpt-4o-mini", "Default model should be gpt-4o-mini"
        assert isinstance(Config.DEBUG, bool), "DEBUG should be a boolean"
    
    def test_config_security_practices(self):
        """Test that configuration follows security best practices"""
        # Test that validation doesn't expose secrets
        validation = Config.validate_required_env_vars()
        validation_str = str(validation)
        assert Config.OPENAI_API_KEY not in validation_str
        assert Config.SUPABASE_KEY not in validation_str
        
        # Test that credentials are not empty or placeholder values
        assert Config.OPENAI_API_KEY != "sk-your-openai-api-key-here"
        assert Config.SUPABASE_URL != "https://your-project-id.supabase.co"
        assert Config.SUPABASE_KEY != "your-supabase-anon-key-here"
        
        # Test that credentials have realistic lengths
        assert len(Config.OPENAI_API_KEY) > 20, "OpenAI API key seems too short"
        assert len(Config.SUPABASE_KEY) > 50, "Supabase key seems too short"
    
    def test_config_environment_isolation(self):
        """Test that configuration properly isolates different environments"""
        # Current config should be for development/testing
        assert Config.DEBUG is True, "Should be in debug mode for testing"
        
        # URLs should point to development resources
        assert "localhost" not in Config.SUPABASE_URL, "Should use real Supabase, not localhost"
        
        # API keys should be development keys (based on project naming)
        assert "test" not in Config.OPENAI_API_KEY.lower() or Config.OPENAI_API_KEY.startswith("sk-proj-"), "Should use real OpenAI credentials for integration testing"


class TestConfigurationFailureScenarios:
    """Test how configuration handles failure scenarios"""
    
    def test_missing_openai_key_handling(self):
        """Test behavior when OpenAI key is missing"""
        original_key = Config.OPENAI_API_KEY
        
        try:
            # Temporarily remove the key
            Config.OPENAI_API_KEY = None
            
            validation = Config.validate_required_env_vars()
            assert validation["status"] == "error"
            assert "OPENAI_API_KEY" in validation["missing_vars"]
            
        finally:
            # Restore the key
            Config.OPENAI_API_KEY = original_key
    
    def test_invalid_supabase_url_handling(self):
        """Test behavior with invalid Supabase URL"""
        original_url = Config.SUPABASE_URL
        
        try:
            # Set invalid URL
            Config.SUPABASE_URL = "invalid-url"
            
            # Should fail to create client
            with pytest.raises(Exception):
                create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                
        finally:
            # Restore the URL
            Config.SUPABASE_URL = original_url
    
    def test_configuration_reload_behavior(self):
        """Test that configuration can be reloaded properly"""
        original_debug = Config.DEBUG
        
        try:
            # Change environment
            os.environ["DEBUG"] = "false" if original_debug else "true"
            
            # Reload configuration
            from importlib import reload
            from app import config
            reload(config)
            
            # Should reflect the change
            assert config.Config.DEBUG != original_debug
            
        finally:
            # Restore original state
            os.environ["DEBUG"] = str(original_debug).lower()
            from importlib import reload
            from app import config
            reload(config) 