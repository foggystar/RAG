from typing import List, Dict, Any

from config import Config
from rag_modules.embedding import get_embedding_async
from rag_modules.get_database import get_database_client
from utils.colored_logger import get_colored_logger

logger = get_colored_logger(__name__)


async def search_async(
    query: List[str],
    included_pdfs : List[str]
) -> List[Dict[str, Any]]:
    """Async version for use with FastAPI"""

    try:
        # 获取查询向量
        query_vectors = await get_embedding_async(query)
        # 创建Milvus客户端
        client = get_database_client()
        
        
        logger.info(f"Searching in collection {Config.DATABASE.collection_name} with {len(query)} queries")

        # 执行搜索 - 使用 Milvus 原生过滤
        search_params = {
            "collection_name": Config.DATABASE.collection_name,
            "data": query_vectors,
            "limit": Config.DEFAULT_SEARCH_LIMIT,
            "filter": f"pdf_name in {included_pdfs}",
            "output_fields": ["pdf_name", "page_number", "text_content"]
        }
        
        results = client.search(**search_params)
        
        logger.info(f"Search completed, found {len(results)} result groups")
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise Exception(f"Search operation failed: {e}")


def search(
    query: List[str],
    included_pdfs : List[str]
) -> List[Dict[str, Any]]:
    """Sync wrapper for backward compatibility"""
    import asyncio
    return asyncio.run(search_async(query, included_pdfs))
