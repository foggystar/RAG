from typing import List, Dict, Optional, Any
from . import reranker, search
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config


def get_reference_with_filter(
        query: str,
        collection_name: Optional[str] = None,
        limit: Optional[int] = None,
        included_pdfs: Optional[List[str]] = None,
        database: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get reference documents with metadata filtering
    
    Args:
        query: Query text
        collection_name: Collection name (uses config default if not provided)
        limit: Result count limit (uses config default if not provided)
        included_pdfs: List of PDF file names to include
        database: Database file path (uses config default if not provided)
    
    Returns:
        List of reranked reference documents
    """
    # Use config defaults if not specified
    if collection_name is None:
        collection_name = Config.DATABASE.collection_name
    if limit is None:
        limit = Config.DEFAULT_SEARCH_LIMIT
    if database is None:
        database = Config.DATABASE.path
    
    # Select search method based on filter conditions
    if included_pdfs:
        # Search only specified PDF files
        if len(included_pdfs) == 1:
            expr = f"pdf_name == '{included_pdfs[0]}'"
        else:
            # For multiple PDFs, use IN operator
            pdf_list_str = "(" + ", ".join([f"'{pdf}'" for pdf in included_pdfs]) + ")"
            expr = f"pdf_name in {pdf_list_str}"
        results = search.search_with_metadata_filter([query], collection_name, limit, expr, database=database)
    else:
        # No filtering
        results = search.search_with_metadata_filter([query], collection_name, limit, database=database)

    # Reranking processing
    rerank_results = []
    if results and len(results) > 0:
        # Extract document text and metadata for reranking
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
        # Filter items with relevance_score below threshold
        filtered_reranked = [item for item in reranked if item.get('relevance_score', 0) >= Config.RELEVANCE_THRESHOLD]
        
        # Build results containing index, relevance, text and metadata
        for i, item in enumerate(filtered_reranked):
            document_index = item.get('index', i)
            if document_index < len(metadata_list):
                metadata = metadata_list[document_index]
                result_dict = {
                    'index': i + 1,  # Index starting from 1
                    'relevance_score': item.get('relevance_score', 0),  # Relevance score
                    'text': documents[document_index] if document_index < len(documents) else item.get('document', ''),  # Related text
                    'pdf_name': metadata['pdf_name'],  # PDF file name
                    'page_number': metadata['page_number'],  # Page number
                    'distance': metadata['distance']  # Vector distance
                }
                rerank_results.append(result_dict)
    
    return rerank_results
