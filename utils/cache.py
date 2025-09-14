"""
Caching utilities for the RAG system using Redis.
Provides caching for query results, PDF processing, and API responses.
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List
from datetime import timedelta
import redis
import structlog
from config import server_settings
from utils.error_handling import RAGException, ErrorCode

logger = structlog.get_logger()


class CacheException(RAGException):
    """Cache-related exceptions"""
    
    def __init__(self, message: str, operation: str):
        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_ERROR,
            details={"operation": operation}
        )


class CacheManager:
    """Redis-based cache manager"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or server_settings.redis_url
        self.ttl = server_settings.redis_ttl
        self.redis_client = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established", redis_url=self.redis_url)
        except Exception as e:
            logger.warning("Redis connection failed, caching disabled", error=str(e))
            self.redis_client = None
    
    def _is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_key = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{hash_key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then as pickle
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                try:
                    return pickle.loads(value.encode())
                except:
                    return value
        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if not self._is_available():
            return False
        
        ttl = ttl or self.ttl
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, int, float, bool, str, type(None))):
                serialized = json.dumps(value)
            else:
                serialized = pickle.dumps(value)
            
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._is_available():
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self._is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Cache clear pattern failed", pattern=pattern, error=str(e))
            return 0
    
    def cache_query_result(self, query: str, pdfs: List[str], result: Any) -> None:
        """Cache query result"""
        cache_key = self._generate_key("query", {"query": query, "pdfs": sorted(pdfs)})
        self.set(cache_key, result, ttl=3600)  # 1 hour cache for queries
    
    def get_cached_query(self, query: str, pdfs: List[str]) -> Optional[Any]:
        """Get cached query result"""
        cache_key = self._generate_key("query", {"query": query, "pdfs": sorted(pdfs)})
        return self.get(cache_key)
    
    def cache_pdf_processing(self, pdf_path: str, processing_result: Any) -> None:
        """Cache PDF processing result"""
        cache_key = self._generate_key("pdf_process", pdf_path)
        self.set(cache_key, processing_result, ttl=86400)  # 24 hours cache for PDF processing
    
    def get_cached_pdf_processing(self, pdf_path: str) -> Optional[Any]:
        """Get cached PDF processing result"""
        cache_key = self._generate_key("pdf_process", pdf_path)
        return self.get(cache_key)
    
    def cache_api_response(self, api_endpoint: str, params: Dict[str, Any], response: Any) -> None:
        """Cache API response"""
        cache_key = self._generate_key("api", {"endpoint": api_endpoint, "params": params})
        self.set(cache_key, response, ttl=1800)  # 30 minutes cache for API responses
    
    def get_cached_api_response(self, api_endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached API response"""
        cache_key = self._generate_key("api", {"endpoint": api_endpoint, "params": params})
        return self.get(cache_key)
    
    def invalidate_pdf_cache(self, pdf_name: str) -> None:
        """Invalidate all cache entries for a specific PDF"""
        patterns = [
            f"pdf_process:*{pdf_name}*",
            f"query:*{pdf_name}*"
        ]
        
        for pattern in patterns:
            deleted_count = self.clear_pattern(pattern)
            if deleted_count > 0:
                logger.info("Invalidated cache entries", pattern=pattern, count=deleted_count)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._is_available():
            return {"available": False}
        
        try:
            info = self.redis_client.info()
            return {
                "available": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            }
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"available": False, "error": str(e)}


# Global cache instance
cache_manager = CacheManager()


def cached_result(prefix: str, ttl: int = None):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_data = {"args": args, "kwargs": kwargs}
            cache_key = cache_manager._generate_key(prefix, cache_data)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit", function=func.__name__, cache_key=cache_key)
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, ttl)
            logger.debug("Cache miss, result cached", function=func.__name__, cache_key=cache_key)
            
            return result
        return wrapper
    return decorator


def cache_query(ttl: int = 3600):
    """Decorator to cache query results"""
    def decorator(func):
        async def wrapper(query: str, pdfs: List[str], *args, **kwargs):
            # Check cache first
            cached_result = cache_manager.get_cached_query(query, pdfs)
            if cached_result is not None:
                logger.info("Query cache hit", query=query, pdfs=pdfs)
                return cached_result
            
            # Execute query
            result = await func(query, pdfs, *args, **kwargs)
            
            # Cache result
            cache_manager.cache_query_result(query, pdfs, result)
            logger.info("Query result cached", query=query, pdfs=pdfs)
            
            return result
        return wrapper
    return decorator