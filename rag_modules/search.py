from pymilvus import MilvusClient
from .embedding import get_embedding, get_batch_embeddings_large_scale
from typing import List, Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search(
    query: List[str],
    database: str = "milvus_rag.db",
    collection_name: str = "demo_collection",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    在Milvus数据库中搜索与查询最相似的向量
    
    Args:
        query: 查询文本列表
        database: 数据库文件路径
        collection_name: 集合名称
        limit: 返回结果数量限制
    
    Returns:
        搜索结果列表
    
    Raises:
        Exception: 当数据库连接失败或搜索失败时抛出异常
    """
    try:
        # 获取查询向量
        query_vectors = get_batch_embeddings_large_scale(query)
        
        # 创建Milvus客户端
        client = MilvusClient(database)
        
        # 检查集合是否存在
        if not client.has_collection(collection_name=collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist in database")
        
        logger.info(f"Searching in collection '{collection_name}' with {len(query)} queries")
        
        # 执行搜索
        res = client.search(
            collection_name=collection_name,  # target collection
            data=query_vectors,  # query vectors
            limit=limit,  # number of returned entities
            output_fields=["text", "subject"],  # specifies fields to be returned
        )
        
        logger.info(f"Search completed, found {len(res)} result groups")
        return res
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise Exception(f"Search operation failed: {e}")

