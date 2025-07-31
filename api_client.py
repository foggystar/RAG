"""
Unified API client factory for the RAG project.
Provides centralized client creation and management for OpenAI-compatible APIs.
"""

from typing import Optional, List, Dict, Any
from openai import OpenAI
import requests
from config import Config, ModelType


class APIClientFactory:
    """Factory for creating and managing API clients"""
    
    _clients = {}
    
    @classmethod
    def get_client(cls, api_key: Optional[str] = None) -> OpenAI:
        """
        Get or create an OpenAI client instance
        
        Args:
            api_key: Optional API key, will use config default if not provided
            
        Returns:
            OpenAI client instance
        """
        if api_key is None:
            api_key = Config.get_api_key()
        
        # Use client caching to avoid creating multiple instances
        if api_key not in cls._clients:
            cls._clients[api_key] = OpenAI(
                api_key=api_key,
                base_url=Config.API_BASE_URL
            )
        
        return cls._clients[api_key]
    
    @classmethod
    def clear_cache(cls):
        """Clear the client cache"""
        cls._clients.clear()


class RerankClient:
    """Specialized client for reranking operations"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.get_api_key()
        self.model_config = Config.get_model_config(ModelType.RERANK)
        self.base_url = Config.API_BASE_URL
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 5,
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量获取文档重排序结果
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回前N个结果
            model: 使用的重排序模型名称，如果不提供则使用配置中的默认模型
        
        Returns:
            重排序结果列表，包含文档索引和分数
        """
        if not documents:
            return []
        
        url = f"{self.base_url}/rerank"
        
        payload = {
            "model": model or self.model_config.name,
            "query": query,
            "documents": documents,
            "top_n": top_n
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get('results', [])
        except Exception as e:
            raise Exception(f"Rerank API request failed: {e}")

class EmbeddingClient:
    """Specialized client for embedding operations"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = APIClientFactory.get_client(api_key)
        self.model_config = Config.get_model_config(ModelType.EMBEDDING)
    
    def create_embedding(self, text: str) -> list[float]:
        """Create embedding for a single text"""
        try:
            response = self.client.embeddings.create(
                model=self.model_config.name,
                input=text,
                encoding_format="float",
                dimensions=self.model_config.dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Embedding API request failed: {e}")
    
    def create_batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts"""
        if not texts:
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.model_config.name,
                input=texts,
                encoding_format="float",
                dimensions=self.model_config.dimensions
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise Exception(f"Batch embedding API request failed: {e}")


class ChatClient:
    """Specialized client for chat/completion operations"""
    
    def __init__(self, api_key: Optional[str] = None, model_type: ModelType = ModelType.CHAT):
        self.client = APIClientFactory.get_client(api_key)
        self.model_config = Config.get_model_config(model_type)
    
    def create_completion(
        self, 
        messages: list[dict], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Create a chat completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_config.name,
                messages=messages,
                max_tokens=max_tokens or self.model_config.max_tokens,
                temperature=temperature or self.model_config.temperature
            )
            
            content = response.choices[0].message.content
            return content if content else "No response generated."
        
        except Exception as e:
            raise Exception(f"Chat completion API request failed: {e}")


class ErrorHandler:
    """Centralized error handling for API operations"""
    
    @staticmethod
    def handle_api_error(operation: str, error: Exception) -> Exception:
        """
        Handle and format API errors consistently
        
        Args:
            operation: The operation that failed
            error: The original exception
            
        Returns:
            Formatted exception with consistent messaging
        """
        error_msg = f"{operation} failed: {str(error)}"
        return Exception(error_msg)