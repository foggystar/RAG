from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import EmbeddingClient
from config import Config


def get_embedding(
    text: str,
    api_key: Optional[str] = None
) -> List[float]:
    """
    Get embedding vector for a single text
    
    Args:
        text: Text to process
        api_key: Optional API key, will use config default if not provided
    
    Returns:
        Embedding vector as list of floats
    """
    client = EmbeddingClient(api_key)
    return client.create_embedding(text)


def get_batch_embeddings(
    texts: List[str],
    api_key: Optional[str] = None
) -> List[List[float]]:
    """
    Get embedding vectors for multiple texts in batch
    
    Args:
        texts: List of texts to process
        api_key: Optional API key, will use config default if not provided
    
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    client = EmbeddingClient(api_key)
    return client.create_batch_embeddings(texts)


def get_batch_embeddings_large_scale(
    texts: List[str],
    api_key: Optional[str] = None,
    max_workers: Optional[int] = None,
    texts_per_worker: Optional[int] = None
) -> List[List[float]]:
    """
    Large-scale concurrent batch embedding generation for hundreds to thousands of texts
    
    Args:
        texts: List of texts to process
        api_key: Optional API key, will use config default if not provided
        max_workers: Maximum concurrent threads (uses config default if not provided)
        texts_per_worker: Texts per worker thread (uses config default if not provided)
    
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    # Use config defaults if not specified
    if max_workers is None:
        max_workers = Config.MAX_CONCURRENT_WORKERS
    if texts_per_worker is None:
        texts_per_worker = Config.TEXTS_PER_WORKER
    
    # For small datasets, use direct batch processing to avoid concurrency overhead
    if len(texts) <= texts_per_worker:
        return get_batch_embeddings(texts, api_key)
    
    def process_chunk(chunk_texts: List[str], chunk_index: int) -> tuple[int, List[List[float]]]:
        """Process a chunk of texts"""
        return chunk_index, get_batch_embeddings(chunk_texts, api_key)
    
    # Split texts into chunks for worker threads
    chunks = []
    for i in range(0, len(texts), texts_per_worker):
        chunk = texts[i:i + texts_per_worker]
        chunks.append((chunk, i // texts_per_worker))
    
    # Dynamically adjust number of workers
    actual_workers = min(max_workers, len(chunks))
    
    # Process chunks using thread pool
    results = {}
    with ThreadPoolExecutor(max_workers=actual_workers) as executor:
        future_to_chunk = {
            executor.submit(process_chunk, chunk_texts, chunk_index): chunk_index
            for chunk_texts, chunk_index in chunks
        }
        
        for future in as_completed(future_to_chunk):
            chunk_index, chunk_embeddings = future.result()
            results[chunk_index] = chunk_embeddings
    
    # Reassemble results in original order
    final_embeddings = []
    for i in range(len(chunks)):
        final_embeddings.extend(results[i])
    
    return final_embeddings