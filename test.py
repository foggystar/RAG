from rag_modules import clear, insert, search, refer, get_database, reranker
# from rag_modules.pdf_manager import PDFManager
from utils import convert, query, chunk
from utils.colored_logger import get_colored_logger
from config import Config, ModelType, DatabaseConfig

logger = get_colored_logger(__name__)

# chunk_res = chunk.load_and_chunk("./docs/74HC165D/74HC165D.md","./docs/74HC165D/74HC165D_meta.json")
# clear.clear_database()

# client = get_database.get_database_client()

# logger.info(f"Collection list: {client.list_collections()}")
# logger.info(f"Collection stats: {client.get_collection_stats(collection_name=DatabaseConfig.collection_name)}")

# insert.insert_data(chunk_res, "74HC165D")


query = ["pin configuration for 74HC165D?"]

search_results = search.search(
    query=query,
    included_pdfs=["74HC165D"]
)



reranked_results = []
for i,result in enumerate(search_results):
    logger.info(f"Searching for Query {i+1}: {query[i]}")
    reranked_index = []
    # 从Hit对象中提取text_content
    contents = [hit.entity.get('text_content') for hit in result]
    reranked_index.append(reranker.get_rerank(query=query[i], documents=contents, top_n=int(Config.DEFAULT_SEARCH_LIMIT/1.3)))

    # print("\nNon Reranking Results:")
    # for doc in list(result):
    #     print("="  * 50)
    #     print(doc['entity'])
    
    logger.info(f"Reranking for query {i+1}")
    entities = [hit.entity.get('entity') for hit in result]
    single_res = []
    for order in reranked_index[i]['results']:
        single_res.append(entities[order['index']])

    reranked_results.append({f"Question {i+1}": query[i], "Reference": single_res})

print(reranked_results)