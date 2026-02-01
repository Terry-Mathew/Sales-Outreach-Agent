"""
Tests for the configuration and settings module.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSettings:
    """Test suite for settings validation."""
    
    def test_weights_must_sum_to_one(self):
        """Scoring weights must sum to 1.0."""
        from pydantic import ValidationError
        from config.settings import Settings
        
        # This should fail validation
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                openai_api_key="sk-test-key-12345",
                rule_score_weight=0.5,
                llm_score_weight=0.6,  # Sum is 1.1, should fail
            )
        
        assert "weights must sum to 1.0" in str(exc_info.value).lower()
    
    def test_valid_weights_accepted(self):
        """Valid weights should be accepted."""
        from config.settings import Settings
        
        settings = Settings(
            openai_api_key="sk-test-key-12345",
            rule_score_weight=0.4,
            llm_score_weight=0.6,
        )
        
        assert settings.rule_score_weight == 0.4
        assert settings.llm_score_weight == 0.6
    
    def test_api_key_required(self):
        """API key must be provided."""
        from pydantic import ValidationError
        from config.settings import Settings
        
        # Clear any existing env var
        original = os.environ.pop("OPENAI_API_KEY", None)
        
        try:
            with pytest.raises(ValidationError):
                Settings()  # No API key provided
        finally:
            if original:
                os.environ["OPENAI_API_KEY"] = original
    
    def test_api_key_minimum_length(self):
        """API key must meet minimum length requirement."""
        from pydantic import ValidationError
        from config.settings import Settings
        
        with pytest.raises(ValidationError):
            Settings(openai_api_key="short")  # Too short
    
    def test_log_level_validation(self):
        """Log level must be a valid option."""
        from pydantic import ValidationError
        from config.settings import Settings
        
        # Valid levels should work
        valid = Settings(
            openai_api_key="sk-test-key-12345",
            log_level="DEBUG"
        )
        assert valid.log_level == "DEBUG"
        
        # Invalid level should fail
        with pytest.raises(ValidationError):
            Settings(
                openai_api_key="sk-test-key-12345",
                log_level="INVALID"
            )
    
    def test_port_range_validation(self):
        """Server port must be in valid range."""
        from pydantic import ValidationError
        from config.settings import Settings
        
        # Valid port
        valid = Settings(
            openai_api_key="sk-test-key-12345",
            gradio_server_port=8080
        )
        assert valid.gradio_server_port == 8080
        
        # Port too low
        with pytest.raises(ValidationError):
            Settings(
                openai_api_key="sk-test-key-12345",
                gradio_server_port=80  # Below 1024
            )
    
    def test_default_values(self):
        """Default values should be set correctly."""
        from config.settings import Settings
        
        settings = Settings(openai_api_key="sk-test-key-12345")
        
        assert settings.primary_model == "gpt-4o-mini"
        assert settings.judge_model == "gpt-4o-mini"
        assert settings.max_retries == 3
        assert settings.enable_caching is True
        assert settings.company_name == "TMP AI Consulting"
