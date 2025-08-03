from rag_modules import clear, insert, query, search, refer, get_database, reranker
# from rag_modules.pdf_manager import PDFManager
from utils.colored_logger import get_colored_logger, logging
from config import Config, ModelType, DatabaseConfig
import ast

logger = get_colored_logger(__name__,level=logging.INFO)

# chunk_res = chunk.load_and_chunk("./docs/74HC165D/74HC165D.md","./docs/74HC165D/74HC165D_meta.json")
# clear.clear_database()

# client = get_database.get_database_client()

# logger.info(f"Collection list: {client.list_collections()}")
# logger.info(f"Collection stats: {client.get_collection_stats(collection_name=DatabaseConfig.collection_name)}")

# insert.insert_data(chunk_res, "74HC165D")


question = "pin configuration for 74HC165D?"

split_query = ast.literal_eval(query.split_query(question))
split_query.insert(0, question)  # Ensure the original question is included

logger.info(f"Split Query Success: {split_query}")

try:
    search_results = list(search.search(
        query=split_query,
        included_pdfs=["74HC165D"]
    ))
except Exception as e:
    print(f"Search operation failed: {e}")


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

    # try:
    #     for order in reranked_index['results']:
    #         hit = result[order['index']]  # 获取对应的hit对象
    #         if(hit.id in de_duplicator):
    #             logger.info(f"Skipping duplicate document ID: {hit.id}")
    #             continue
    #         de_duplicator.add(hit.id)
    #         all_docs.append(hit.entity['entity'])
    # except Exception as e:
    #     logger.error(f"Reranking failed for query {i+1}: {e}")

"""
Data structure:
[
  {'Question': ... , 'Reference': [...]},
  ...
]
"""
# for one in all_docs:
#     print(one)
print(query.generate_answer(questions=split_query,reference=all_docs))
