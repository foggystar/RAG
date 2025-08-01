from rag_modules import clear, insert, search, refer, get_database, reranker
# from rag_modules.pdf_manager import PDFManager
from utils import convert, query, chunk
from utils.colored_logger import get_colored_logger
from config import Config, ModelType, DatabaseConfig

logger = get_colored_logger(__name__)

chunk_res = chunk.load_and_chunk("./docs/74HC165D/74HC165D.md","./docs/74HC165D/74HC165D_meta.json")
clear.clear_database()

client = get_database.get_database_client()

logger.info(f"Collection list: {client.list_collections()}")
logger.info(f"Collection stats: {client.get_collection_stats(collection_name=DatabaseConfig.collection_name)}")

insert.insert_data(chunk_res, "74HC165D")


query = ["pin configuration for 74HC165D?"]

search_results = search.search(
    query=query,
    included_pdfs=["74HC165D"]
)


reranked_results = []
for i,result in enumerate(search_results):
    print(f"Query {i+1}: {query[i]}")
    # 从Hit对象中提取text_content
    documents = [hit.entity.get('text_content') for hit in result]
    reranked_results.append(reranker.get_rerank(query=query[i], documents=documents, top_n=Config.DEFAULT_SEARCH_LIMIT))

    print("\nNon Reranking Results:")
    for doc in list(result):
        print("="  * 50)
        print(doc)
    
    print("\nReranking Results:")
    for i,_ in enumerate(reranked_results[i]['results']):
        print("="  * 50)
        print(list(result)[i])
