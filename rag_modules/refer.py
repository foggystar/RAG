from typing import List, Dict, Optional
from . import reranker, search


def get_reference_with_filter(
        query: str,
        collection_name: str = "rag_docs",
        limit: int = 10,
        included_pdfs: Optional[List[str]] = None,
        database: str = "milvus_rag.db"
) -> List[Dict[str, any]]:
    """
    获取带有元数据过滤的参考文档
    
    Args:
        query: 查询文本
        collection_name: 集合名称
        limit: 返回结果数量限制
        included_pdfs: 要使用的PDF文件名列表
        database: 数据库文件路径
    
    Returns:
        重排序后的参考文档列表
    """
    
    # 根据过滤条件选择搜索方法
    if included_pdfs:
        # 只搜索指定的PDF文件
        if len(included_pdfs) == 1:
            expr = f"pdf_name == '{included_pdfs[0]}'"
        else:
            # 对于多个PDF，使用 IN
            pdf_list_str = "(" + ", ".join([f"'{pdf}'" for pdf in included_pdfs]) + ")"
            expr = f"pdf_name in {pdf_list_str}"
        results = search.search_with_metadata_filter([query], collection_name, limit, expr, database=database)
    else:
        # 不使用任何过滤
        results = search.search_with_metadata_filter([query], collection_name, limit, database=database)

    # 重排序处理
    rerank_results = []
    if results and len(results) > 0:
        # 提取文档文本和元数据用于重排序
        documents = []
        metadata_list = []
        for hit in results[0]:
            entity = hit.get('entity', {})
            documents.append(entity.get('text_content', ''))
            metadata_list.append({
                'pdf_name': entity.get('pdf_name', ''),
                'page_number': entity.get('page_number', 0),
                'distance': hit.get('distance', 0)
            })
        
        reranked = reranker.get_rerank(query, documents, top_n=min(5, len(documents)))
        # 过滤relevance_score低于0.2的项
        filtered_reranked = [item for item in reranked if item.get('relevance_score', 0) >= 0.2]
        
        # 构建包含序号、关联度、文本和元数据的结果
        for i, item in enumerate(filtered_reranked):
            document_index = item.get('index', i)
            if document_index < len(metadata_list):
                metadata = metadata_list[document_index]
                result_dict = {
                    'index': i + 1,  # 序号，从1开始
                    'relevance_score': item.get('relevance_score', 0),  # 关联度
                    'text': documents[document_index] if document_index < len(documents) else item.get('document', ''),  # 相关文本
                    'pdf_name': metadata['pdf_name'],  # PDF文件名
                    'page_number': metadata['page_number'],  # 页码
                    'distance': metadata['distance']  # 向量距离
                }
                rerank_results.append(result_dict)
    
    return rerank_results
