from typing import List, Optional
from pymilvus import MilvusClient
from .embedding import get_batch_embeddings_large_scale
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置彩色日志
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)

from config import Config, ModelType


def insert_data_with_metadata(
    texts: List[str], 
    pdf_names: List[str],
    page_numbers: List[int],
    is_blocked_list: Optional[List[bool]] = None,
    database: Optional[str] = None, 
    collection_name: Optional[str] = None
) -> bool:
    """
    Insert data with metadata into Milvus collection
    
    Args:
        texts: List of text content
        pdf_names: List of PDF file names
        page_numbers: List of page numbers
        is_blocked_list: List of blocked status (defaults to False for all)
        database: Database file path (uses config default if not provided)
        collection_name: Collection name (uses config default if not provided)
    
    Returns:
        Whether the operation was successful
    """
    # Use config defaults if not specified
    if database is None:
        database = Config.DATABASE.path
    if collection_name is None:
        collection_name = Config.DATABASE.collection_name
    
    if is_blocked_list is None:
        is_blocked_list = [False] * len(texts)
    
    # Validate input length consistency
    if not (len(texts) == len(pdf_names) == len(page_numbers) == len(is_blocked_list)):
        raise ValueError("All input lists must have the same length")
    
    try:
        # Create Milvus client
        client = MilvusClient(database)
        
        # Check if collection exists, create with metadata if it doesn't
        if not client.has_collection(collection_name=collection_name):
            logger.info(f"Collection '{collection_name}' does not exist, creating new collection...")
            # Create collection with metadata for MilvusClient
            client.create_collection(
                collection_name=collection_name,
                dimension=Config.MODELS[ModelType.EMBEDDING].dimensions,
                id_type="int",
                primary_field_name="id",
                vector_field_name="vector"
            )
            logger.info(f"Collection '{collection_name}' created successfully")
        
        # Get embedding vectors
        logger.info(f"Generating embedding vectors for {len(texts)} texts...")
        embeddings = get_batch_embeddings_large_scale(texts)
        logger.info(f"Embedding vector generation completed")
        
        # Prepare data for insertion - adapt to MilvusClient format
        data = []
        for i in range(len(texts)):
            data.append({
                "id": i,
                "vector": embeddings[i],
                "text_content": texts[i],
                "pdf_name": pdf_names[i],
                "page_number": page_numbers[i],
                "is_blocked": is_blocked_list[i]
            })
        
        # Execute insertion operation
        logger.info(f"Inserting {len(data)} records into collection '{collection_name}'...")
        res = client.insert(collection_name=collection_name, data=data)
        
        logger.info(f"Data insertion completed, inserted {len(texts)} records")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        return False