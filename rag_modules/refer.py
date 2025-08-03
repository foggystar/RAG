from typing import List, Dict, Any

from config import Config
from rag_modules import reranker, search
from utils.colored_logger import get_colored_logger, logging

logger = get_colored_logger(__name__,level=logging.INFO)


async def get_reference(
        split_query: List[str],
        included_pdfs: List[str]
) -> List[Dict[str, Any]]:
    
    try:
        search_results = await search.search_async(
                query=split_query,
                included_pdfs=included_pdfs
        )
    except Exception as e:
        logger.error(f"Search operation failed: {e}")
        return []

    all_docs = []
    # de_duplicator = set()  # 用于去重
    pre_de_duplicator = set()
    for i,result in enumerate(search_results):
        logger.info(f"Searching for Query {i+1}: {split_query[i]}")
        reranked_index = []
        contents = []
        for hit in result:
            if hit.id in pre_de_duplicator:
                logger.info(f"Pre Skipping duplicate document ID: {hit.id}")
                continue
            pre_de_duplicator.add(hit.id)
            contents.append(hit.entity.get('text_content'))  # 获取文本内容，避免KeyError
        # contents = [hit.entity.get('text_content') for hit in result]
        if not contents:
            logger.warning(f"No contents found for query {i+1}. Skipping reranking.")
            continue

        reranked_index = reranker.get_rerank(query=str(split_query[i]), documents=contents, top_n=int(Config.DEFAULT_RERANK_LIMIT))
        
        logger.info(f"Reranking for query {i+1}\n")
        try:
            for order in reranked_index['results']:
                hit = result[order['index']]
                all_docs.append(hit.entity['entity'])
        except Exception as e:
            logger.error(f"Reranking failed for query {i+1}: {e}")
    return all_docs


def get_reference_sync(
        split_query: List[str],
        included_pdfs: List[str]
) -> List[Dict[str, Any]]:
    """Synchronous version for backward compatibility"""
    import asyncio
    return asyncio.run(get_reference(split_query, included_pdfs))