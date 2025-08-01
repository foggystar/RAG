from pymilvus import MilvusClient, Collection, connections
from .embedding import get_embedding, get_batch_embeddings_large_scale
from typing import List, Dict, Any, Optional
import logging
import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置彩色日志
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)


def search_with_metadata_filter(
    query: List[str],
    collection_name: str = "rag_docs",
    limit: int = 10,
    expr: Optional[str] = None,
    output_fields: Optional[List[str]] = None,
    database: str = "milvus_rag.db"
) -> List[Dict[str, Any]]:
    """
    在Milvus数据库中搜索与查询最相似的向量，支持元数据过滤
    
    Args:
        query: 查询文本列表
        collection_name: 集合名称
        limit: 返回结果数量限制
        expr: 过滤表达式，例如: "is_blocked == false" 或 "pdf_name != 'secret.pdf'"
        output_fields: 要返回的字段列表，默认为 ["text_content", "pdf_name", "page_number"]
        database: 数据库文件路径
    
    Returns:
        搜索结果列表
    
    Raises:
        Exception: 当数据库连接失败或搜索失败时抛出异常
    """
    if output_fields is None:
        output_fields = ["text_content", "pdf_name", "page_number", "is_blocked"]
    
    try:
        # 获取查询向量
        query_vectors = get_batch_embeddings_large_scale(query)
        
        # 创建Milvus客户端
        client = MilvusClient(database)
        
        # 检查集合是否存在
        if not client.has_collection(collection_name=collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist in database")
        
        logger.info(f"Searching in collection '{collection_name}' with {len(query)} queries")
        if expr:
            logger.info(f"Using filter expression: {expr}")
        
        # 执行搜索 - 使用 Milvus 原生过滤
        search_params = {
            "collection_name": collection_name,
            "data": query_vectors,
            "limit": limit,
            "output_fields": output_fields
        }
        
        # 如果有过滤表达式，添加到搜索参数中
        if expr:
            search_params["filter"] = expr
        
        results = client.search(**search_params)
        
        logger.info(f"Search completed, found {len(results)} result groups")
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise Exception(f"Search operation failed: {e}")


def search_only_unblocked(
    query: List[str],
    collection_name: str = "rag_docs",
    limit: int = 10,
    database: str = "milvus_rag.db"
) -> List[Dict[str, Any]]:
    """
    只搜索未被屏蔽的文档
    
    Args:
        query: 查询文本列表
        collection_name: 集合名称
        limit: 返回结果数量限制
        database: 数据库文件路径
    
    Returns:
        搜索结果列表
    """
    expr = "is_blocked == false"
    return search_with_metadata_filter(query, collection_name, limit, expr, database=database)


def simple_search(
    query: List[str],
    collection_name: str = "demo_collection",
    filter_expr: Optional[str] = None,
    limit: int = 10,
    output_fields: Optional[List[str]] = None,
    database: str = "milvus_rag.db"
) -> List[Dict[str, Any]]:
    """
    简化的搜索函数，模仿 sample.py 的用法
    
    Args:
        query: 查询文本列表
        collection_name: 集合名称
        filter_expr: 过滤表达式，例如: "subject == 'biology'"
        limit: 返回结果数量限制
        output_fields: 要返回的字段列表
        database: 数据库文件路径
    
    Returns:
        搜索结果列表
        
    Example:
        # 类似 sample.py 的用法
        results = simple_search(
            query=["tell me AI related information"],
            filter_expr="subject == 'biology'",
            limit=2,
            output_fields=["text", "subject"]
        )
    """
    try:
        # 获取查询向量
        query_vectors = get_batch_embeddings_large_scale(query)
        
        # 创建Milvus客户端
        client = MilvusClient(database)
        
        # 检查集合是否存在
        if not client.has_collection(collection_name=collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist in database")
        
        logger.info(f"Performing simple search in collection '{collection_name}'")
        if filter_expr:
            logger.info(f"Using filter: {filter_expr}")
        
        # Build search parameters
        search_params = {
            "collection_name": collection_name,
            "data": query_vectors,
            "limit": limit
        }
        
        if filter_expr:
            search_params["filter"] = filter_expr
            
        if output_fields:
            search_params["output_fields"] = output_fields
        
        # Execute search
        results = client.search(**search_params)
        
        logger.info(f"Simple search completed, found {len(results)} result groups")
        return results
        
    except Exception as e:
        logger.error(f"Simple search failed: {e}")
        raise Exception(f"Simple search operation failed: {e}")



