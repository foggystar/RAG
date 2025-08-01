from .embedding import get_embedding
from .get_database import get_database_client
from typing import List, Dict, Any, Optional
import logging
import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, DatabaseConfig
# 设置彩色日志
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)


def search(
    query: List[str],
    included_pdfs : List[str]
) -> List[Dict[str, Any]]:

    try:
        # 获取查询向量
        query_vectors = get_embedding(query)
        # 创建Milvus客户端
        client = get_database_client()
        
        
        logger.info(f"Searching in collection '{DatabaseConfig.collection_name}' with {len(query)} queries")

        # 执行搜索 - 使用 Milvus 原生过滤
        search_params = {
            "collection_name": DatabaseConfig.collection_name,
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
