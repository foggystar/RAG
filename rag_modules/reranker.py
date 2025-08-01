"""
Reranker module for the RAG project.
Provides document reranking functionality using configured models and API clients.
"""

from typing import List, Optional, Dict, Any
import requests
from config import Config, ModelType
from api_client import RerankClient

def get_rerank(
    query: str,
    documents: List[str],
    top_n: int = Config.DEFAULT_SEARCH_LIMIT / 2,
) -> List[Dict[str, Any]]:
    """
    便捷函数：批量获取文档重排序结果
    
    Args:
        query: 查询文本
        documents: 文档列表
        top_n: 返回前N个结果
        model: 使用的重排序模型名称，如果不提供则使用配置中的默认模型
        api_key: API密钥，如果不提供则使用配置中的默认值
    
    Returns:
        重排序结果列表，包含文档索引和分数
    """
    client = RerankClient()
    return client.rerank(query, documents, top_n)