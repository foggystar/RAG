from typing import List, Dict
from . import reranker, search


def get_reference(
        query: str,
        database: str = "milvus_rag.db",
        collection_name: str = "demo_collection",
        limit: int = 10
) -> List[Dict[str, any]]:

    results = search.search([query], database, collection_name, limit)  # 搜索数据，将query包装成列表

    # 重排序处理
    rerank_results = []
    if results and len(results) > 0:
        # 提取文档文本用于重排序，results[0]是第一个查询的结果
        documents = [hit['entity']['text'] for hit in results[0]]
        reranked = reranker.get_rerank(query, documents, top_n=min(5, len(documents)))
        # 过滤relevance_score低于0.2的项
        filtered_reranked = [item for item in reranked if item.get('relevance_score', 0) >= 0.2]
        
        # 构建包含序号、关联度和文本的结果
        for i, item in enumerate(filtered_reranked):
            # 从原始文档中获取文本内容
            document_index = item.get('index', i)
            result_dict = {
                'index': i + 1,  # 序号，从1开始
                'relevance_score': item.get('relevance_score', 0),  # 关联度
                'text': documents[document_index] if document_index < len(documents) else item.get('document', '')  # 相关文本
            }
            rerank_results.append(result_dict)
    else:
        rerank_results = []
    
    # print("\nRerank Results:")
    # print(f"Query reranked results:")
    # for result in rerank_results:
    #     print(f"  - 序号: {result['index']}, 关联度: {result['relevance_score']:.3f}, 文本: {result['text'][:100]}...")
    
    return rerank_results
