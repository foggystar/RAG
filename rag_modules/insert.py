from typing import List, Dict, Any

from config import Config
from rag_modules.embedding import get_embedding_async
from rag_modules.get_database import get_database_client
from utils.colored_logger import get_colored_logger

logger = get_colored_logger(__name__)


async def insert_data(
    data : List[Dict[str, Any]],
    pdf_name: str,
) -> bool:
    
    # titled_text = [("Title: " + data[i]['metadata']['title'] + "Content: " + data[i]['content']) for i in range(len(data))]
    titled_text = [("Content: " + data[i]['content']) for i in range(len(data))]

    page_id = [data[i]['metadata']['page_id'] for i in range(len(data))]
    try:
        client = get_database_client()

        logger.info(f"Generating embedding vectors for {len(data)} texts")
        embeddings = await get_embedding_async(titled_text)
        logger.info(f"Embedding vector generation completed")
        
    except Exception as e:
        logger.error(f"Failed to embed data: {e}")
        return False
    
    try:
        insert_data = [
            {
                "vector": embeddings[i],
                "text_content": titled_text[i],
                "pdf_name": pdf_name,
                "page_number": page_id[i],
            }
            for i in range(len(data))
        ]
        # Execute insertion operation
        logger.info(f"Inserting {len(data)} records into collection '{Config.DATABASE.collection_name}'...")
        client.insert(collection_name=Config.DATABASE.collection_name, data=insert_data)
        
        logger.info(f"Data insertion completed, inserted {len(data)} records")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        return False