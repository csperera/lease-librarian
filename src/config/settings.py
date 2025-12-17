"""
Lease Digitizer - Configuration Settings Module

This module provides centralized configuration management using Pydantic Settings.
It handles environment variable loading, validation, and provides typed access
to all application configuration.

Features:
- Environment variable loading with .env file support
- Type validation for all configuration values
- Sensible defaults for development
- Easy access to LLM, database, and application settings
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or a .env file.
    The settings are cached using lru_cache for performance.
    
    Example:
        >>> settings = get_settings()
        >>> print(settings.openai_model)
        'gpt-4-turbo-preview'
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # -------------------------------------------------------------------------
    # OpenAI Configuration
    # -------------------------------------------------------------------------
    openai_api_key: SecretStr = Field(
        ...,
        description="OpenAI API key for LLM access"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for agents"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model for embeddings"
    )
    
    # -------------------------------------------------------------------------
    # LangChain Configuration
    # -------------------------------------------------------------------------
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing"
    )
    langchain_api_key: SecretStr | None = Field(
        default=None,
        description="LangSmith API key for tracing"
    )
    langchain_project: str = Field(
        default="lease-digitizer",
        description="LangSmith project name"
    )
    
    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment"
    )
    
    # -------------------------------------------------------------------------
    # Database Configuration
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="sqlite:///./data/lease_digitizer.db",
        description="Database connection URL"
    )
    
    # -------------------------------------------------------------------------
    # Vector Store Configuration
    # -------------------------------------------------------------------------
    chroma_persist_directory: str = Field(
        default="./data/chroma",
        description="ChromaDB persistence directory"
    )
    
    # -------------------------------------------------------------------------
    # Document Processing
    # -------------------------------------------------------------------------
    max_document_size_mb: int = Field(
        default=50,
        description="Maximum document size in megabytes"
    )
    supported_file_types: str = Field(
        default="pdf,docx",
        description="Comma-separated list of supported file types"
    )
    
    # -------------------------------------------------------------------------
    # Streamlit Configuration
    # -------------------------------------------------------------------------
    streamlit_server_port: int = Field(
        default=8501,
        description="Streamlit server port"
    )
    streamlit_server_address: str = Field(
        default="localhost",
        description="Streamlit server address"
    )
    
    @property
    def supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return [ext.strip().lower() for ext in self.supported_file_types.split(",")]
    
    @property
    def max_document_size_bytes(self) -> int:
        """Get maximum document size in bytes."""
        return self.max_document_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application settings instance
        
    Note:
        Settings are cached after first load. Call `get_settings.cache_clear()`
        to reload settings if environment variables change.
    """
    return Settings()


# TODO: Add settings validation on startup
# TODO: Add support for secrets management (AWS Secrets Manager, HashiCorp Vault)
# TODO: Add configuration profiles for different environments
