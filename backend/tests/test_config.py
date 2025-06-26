import os
import pytest
from app.config import Config


def test_config_loads_environment_variables():
    """Test that Config class can load environment variables"""
    # Test that Config class exists and has expected attributes
    assert hasattr(Config, 'OPENAI_API_KEY')
    assert hasattr(Config, 'OPENAI_MODEL')
    assert hasattr(Config, 'SUPABASE_URL')
    assert hasattr(Config, 'SUPABASE_KEY')
    assert hasattr(Config, 'DEBUG')


def test_config_default_values():
    """Test that Config has proper default values"""
    # Test default model
    assert Config.OPENAI_MODEL == "gpt-4-turbo-preview"
    
    # Test default debug (should be False if not set)
    if not os.getenv("DEBUG"):
        assert Config.DEBUG is False


def test_config_validation_method():
    """Test that config validation method exists and works"""
    # Test that validation method exists
    assert hasattr(Config, 'validate_required_env_vars')
    
    # Test that validation returns proper structure
    result = Config.validate_required_env_vars()
    assert isinstance(result, dict)
    assert "status" in result
    
    # Status should be either "ok" or "error"
    assert result["status"] in ["ok", "error"]
    
    if result["status"] == "error":
        assert "missing_vars" in result
        assert isinstance(result["missing_vars"], list)
    else:
        assert "message" in result


def test_config_debug_parsing():
    """Test that DEBUG environment variable is parsed correctly"""
    # Save original value
    original_debug = os.getenv("DEBUG")
    
    try:
        # Test True values
        for true_val in ["true", "True", "TRUE"]:
            os.environ["DEBUG"] = true_val
            # Reload config
            from importlib import reload
            from app import config
            reload(config)
            assert config.Config.DEBUG is True
        
        # Test False values
        for false_val in ["false", "False", "FALSE", ""]:
            os.environ["DEBUG"] = false_val
            reload(config)
            assert config.Config.DEBUG is False
            
    finally:
        # Restore original value
        if original_debug is not None:
            os.environ["DEBUG"] = original_debug
        elif "DEBUG" in os.environ:
            del os.environ["DEBUG"] 