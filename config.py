"""
Centralized configuration module for the RAG project.
Manages all model settings, API configurations, and database settings.
"""

import os
from typing import Optional
from dataclasses import dataclass
from enum import Enum


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
    path: str = "milvus_rag.db"
    collection_name: str = "rag_docs"


class Config:
    """Centralized configuration manager"""
    
    # API Configuration
    API_BASE_URL = "https://api.siliconflow.cn/v1"
    API_KEY_ENV_VAR = "siliconflow_api_key"
    
    # Model Configurations
    MODELS = {
        ModelType.EMBEDDING: ModelConfig(
            name="Qwen/Qwen3-Embedding-4B",
            dimensions=768
        ),
        ModelType.SPLIT: ModelConfig(
            name="Qwen/Qwen3-30B-A3B",
            max_tokens=1000,
            temperature=0.7
        ),
        ModelType.CHAT: ModelConfig(
            name="moonshotai/Kimi-K2-Instruct",
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
    DEFAULT_SEARCH_LIMIT = 10
    
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
    
    