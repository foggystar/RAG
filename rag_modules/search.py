from pymilvus import MilvusClient, Collection, connections
from .embedding import get_embedding, get_batch_embeddings_large_scale
from typing import List, Dict, Any, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        
        # 执行搜索
        results = client.search(
            collection_name=collection_name,
            data=query_vectors,
            limit=limit * 2,  # 获取更多结果以便过滤
            output_fields=output_fields
            # 注意：MilvusClient (Lite) 可能不支持复杂的过滤表达式
            # 如果需要过滤，可能需要在结果中手动过滤
        )
        
        # 手动应用过滤逻辑
        if expr:
            filtered_results = []
            for query_results in results:
                filtered_query_results = []
                for hit in query_results:
                    entity = hit.get('entity', {})
                    # 简单的过滤逻辑实现
                    if _apply_filter(entity, expr):
                        filtered_query_results.append(hit)
                    if len(filtered_query_results) >= limit:
                        break
                filtered_results.append(filtered_query_results)
            results = filtered_results
        
        logger.info(f"Search completed, found {len(results)} result groups")
        return results
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise Exception(f"Search operation failed: {e}")


def _apply_filter(entity: dict, expr: str) -> bool:
    """
    手动应用过滤表达式
    
    Args:
        entity: 实体数据
        expr: 过滤表达式
    
    Returns:
        是否通过过滤
    """
    try:
        # 简单的过滤逻辑实现
        if "is_blocked == false" in expr:
            if entity.get('is_blocked', True):
                return False
        
        if "is_blocked == true" in expr:
            if not entity.get('is_blocked', False):
                return False
        
        # 处理 pdf_name 过滤
        if "pdf_name !=" in expr:
            # 提取要排除的PDF名称
            import re
            matches = re.findall(r"pdf_name != '([^']+)'", expr)
            for pdf_name in matches:
                if entity.get('pdf_name', '') == pdf_name:
                    return False
        
        if "pdf_name not in" in expr:
            # 提取要排除的PDF列表
            import re
            match = re.search(r"pdf_name not in \(([^)]+)\)", expr)
            if match:
                pdf_list_str = match.group(1)
                excluded_pdfs = [pdf.strip(" '\"") for pdf in pdf_list_str.split(',')]
                if entity.get('pdf_name', '') in excluded_pdfs:
                    return False
        
        return True
        
    except Exception:
        # 如果过滤失败，返回True（不过滤）
        return True


# def search_exclude_pdfs(
#     query: List[str],
#     excluded_pdfs: List[str],
#     collection_name: str = "rag_docs",
#     limit: int = 10
# ) -> List[Dict[str, Any]]:
#     """
#     搜索时排除指定的PDF文件
    
#     Args:
#         query: 查询文本列表
#         excluded_pdfs: 要排除的PDF文件名列表
#         collection_name: 集合名称
#         limit: 返回结果数量限制
    
#     Returns:
#         搜索结果列表
#     """
#     if not excluded_pdfs:
#         # 如果没有要排除的PDF，直接搜索
#         return search_with_metadata_filter(query, collection_name, limit)
    
#     # 构建过滤表达式
#     if len(excluded_pdfs) == 1:
#         expr = f"pdf_name != '{excluded_pdfs[0]}'"
#     else:
#         # 对于多个PDF，使用 NOT IN
#         pdf_list_str = "(" + ", ".join([f"'{pdf}'" for pdf in excluded_pdfs]) + ")"
#         expr = f"pdf_name not in {pdf_list_str}"
    
#     return search_with_metadata_filter(query, collection_name, limit, expr)


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


# def search(
#     query: List[str],
#     database: str = "milvus_rag.db",
#     collection_name: str = "demo_collection",
#     limit: int = 10
# ) -> List[Dict[str, Any]]:
#     """
#     在Milvus数据库中搜索与查询最相似的向量 (保持向后兼容性)
    
#     Args:
#         query: 查询文本列表
#         database: 数据库文件路径
#         collection_name: 集合名称
#         limit: 返回结果数量限制
    
#     Returns:
#         搜索结果列表
    
#     Raises:
#         Exception: 当数据库连接失败或搜索失败时抛出异常
#     """
#     try:
#         # 获取查询向量
#         query_vectors = get_batch_embeddings_large_scale(query)
        
#         # 创建Milvus客户端
#         client = MilvusClient(database)
        
#         # 检查集合是否存在
#         if not client.has_collection(collection_name=collection_name):
#             raise Exception(f"Collection '{collection_name}' does not exist in database")
        
#         logger.info(f"Searching in collection '{collection_name}' with {len(query)} queries")
        
#         # 执行搜索
#         res = client.search(
#             collection_name=collection_name,  # target collection
#             data=query_vectors,  # query vectors
#             limit=limit,  # number of returned entities
#             output_fields=["text", "subject"],  # specifies fields to be returned
#         )
        
#         logger.info(f"Search completed, found {len(res)} result groups")
#         return res
        
#     except Exception as e:
#         logger.error(f"Search failed: {e}")
#         raise Exception(f"Search operation failed: {e}")

