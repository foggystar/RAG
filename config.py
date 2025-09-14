"""
Centralized configuration module for the RAG project.
Manages all model settings, API configurations, and database settings.
"""

import os
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum
from pydantic_settings import BaseSettings


class ModelType(Enum):
    """Supported model types"""
    EMBEDDING = "embedding"
    SPLIT = "split"
    CHAT = "chat"
    RERANK = "rerank"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    dimensions: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "database/milvus_rag.db"
    collection_name: str = "rag_docs"
    dimensions: int = 2048
    chunk_size_limit: int = 2000

class Config:
    """Centralized configuration manager"""
    
    # API Configuration
    API_BASE_URL = "https://api.siliconflow.cn/v1"
    API_KEY_ENV_VAR = "siliconflow_api_key"

    # Marker Configuration
    MODEL_DIR = "/home/foggystar/Projects/RAG/models"
    
    # Model Configurations
    MODELS = {
        ModelType.EMBEDDING: ModelConfig(
            name="Qwen/Qwen3-Embedding-4B",
            dimensions=DatabaseConfig.dimensions
        ),
        ModelType.SPLIT: ModelConfig(
            name="Qwen/Qwen3-30B-A3B-Instruct-2507",
            max_tokens=1000,
            temperature=0.7,
        ),
        ModelType.CHAT: ModelConfig(
            name="deepseek-ai/DeepSeek-V3",
            max_tokens=50000,
            temperature=0.6
        ),
        ModelType.RERANK: ModelConfig(
            name="Qwen/Qwen3-Reranker-4B",
            max_tokens=10000,
            temperature=0.1
        )
    }
    
    # Database Configuration
    DATABASE = DatabaseConfig()
    
    # Processing Configuration
    MAX_CONCURRENT_WORKERS = 3
    TEXTS_PER_WORKER = 100
    RELEVANCE_THRESHOLD = 0.2
    DEFAULT_SEARCH_LIMIT = 15
    DEFAULT_RERANK_LIMIT = 5
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get API key from environment variables"""
        api_key = os.getenv(cls.API_KEY_ENV_VAR)
        if not api_key:
            raise ValueError(
                f"API key not found. Please set {cls.API_KEY_ENV_VAR} environment variable."
            )
        return api_key
    
    @classmethod
    def get_model_config(cls, model_type: ModelType) -> ModelConfig:
        """Get configuration for a specific model type"""
        return cls.MODELS[model_type]
    
    @classmethod
    def get_embedding_model(cls) -> str:
        """Get embedding model name"""
        return cls.MODELS[ModelType.EMBEDDING].name
    
    @classmethod
    def get_split_model(cls) -> str:
        """Get embedding model name"""
        return cls.MODELS[ModelType.SPLIT].name

    @classmethod
    def get_chat_model(cls) -> str:
        """Get chat model name"""
        return cls.MODELS[ModelType.CHAT].name
    
    @classmethod
    def get_rerank_model(cls) -> str:
        """Get rerank model name"""
        return cls.MODELS[ModelType.RERANK].name


class ServerSettings(BaseSettings):
    """Server configuration settings"""
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # File upload settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = [".pdf"]
    upload_dir: str = "uploads"
    
    # Redis settings (for caching)
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 3600  # 1 hour
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class SecuritySettings(BaseSettings):
    """Security configuration"""
    # File security
    allowed_filename_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
    max_filename_length: int = 255
    
    # Path security
    base_upload_dir: str = "uploads"
    allowed_base_dirs: List[str] = ["uploads", "static", "docs"]
    
    # API security
    max_query_length: int = 2000
    max_pdfs_per_query: int = 10
    timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"


# Global settings instances
server_settings = ServerSettings()
security_settings = SecuritySettings()
    
    