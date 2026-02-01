"""
TMP AI Sales Agent - Configuration Settings
Uses Pydantic for validation and type safety.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Literal, Optional
from pathlib import Path
import os


class Settings(BaseSettings):
    """
    Application settings with environment variable support and validation.
    All settings can be overridden via environment variables or .env file.
    """
    
    # --- API Keys ---
    openai_api_key: str = Field(
        ..., 
        min_length=10, 
        description="OpenAI API key for LLM calls"
    )
    
    # --- Model Configuration ---
    primary_model: str = Field(
        default="gpt-4o-mini",
        description="Primary model for SDR agents"
    )
    judge_model: str = Field(
        default="gpt-4o-mini",
        description="Model for email evaluation"
    )
    fallback_model: str = Field(
        default="gpt-3.5-turbo",
        description="Fallback model if primary fails"
    )
    
    # --- Agent Behavior ---
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for failed API calls"
    )
    request_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Request timeout in seconds"
    )
    enable_caching: bool = Field(
        default=True,
        description="Enable response caching"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="Cache time-to-live in seconds"
    )
    
    # --- Scoring Weights ---
    rule_score_weight: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Weight for rule-based scoring (0-1)"
    )
    llm_score_weight: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Weight for LLM-based scoring (0-1)"
    )
    llm_fallback_score: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Fallback score when LLM evaluation fails"
    )
    
    @model_validator(mode='after')
    def validate_weights_sum_to_one(self) -> 'Settings':
        """Ensure scoring weights sum to 1.0"""
        total = self.rule_score_weight + self.llm_score_weight
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f'Scoring weights must sum to 1.0, got {total:.2f} '
                f'(rule={self.rule_score_weight}, llm={self.llm_score_weight})'
            )
        return self
    
    # --- Cost Tracking ---
    estimated_cost_per_call: float = Field(
        default=0.002,
        ge=0.0,
        description="Estimated cost per API call in USD"
    )
    enable_cost_alerts: bool = Field(
        default=True,
        description="Enable cost threshold alerts"
    )
    max_cost_per_run: float = Field(
        default=0.50,
        ge=0.0,
        description="Maximum allowed cost per run in USD"
    )
    
    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing"
    )
    
    # --- UI Configuration ---
    gradio_server_port: int = Field(
        default=7860,
        ge=1024,
        le=65535,
        description="Gradio server port"
    )
    gradio_share: bool = Field(
        default=False,
        description="Enable Gradio public sharing"
    )
    
    # --- Company Configuration ---
    company_name: str = Field(
        default="TMP AI Consulting",
        description="Company name for email branding"
    )
    
    # --- Paths ---
    @property
    def project_root(self) -> Path:
        """Get the project root directory"""
        return Path(__file__).parent.parent
    
    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory path"""
        return self.project_root / "config" / "prompts"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignore extra fields in .env
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """
    Factory function to get settings instance.
    Useful for dependency injection and testing.
    """
    return Settings()


# Singleton instance for easy import
try:
    settings = Settings()
except Exception as e:
    # Provide helpful error message for missing configuration
    import sys
    print(f"❌ Configuration Error: {e}", file=sys.stderr)
    print("💡 Tip: Copy .env.example to .env and fill in your API keys", file=sys.stderr)
    raise
