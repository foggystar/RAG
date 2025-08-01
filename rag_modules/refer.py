from typing import List, Dict, Optional, Any
from . import reranker, search
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def get_reference(
        query: str,
        included_pdfs: List[str]
) -> List[Dict[str, Any]]:
    
    search_results = search.search(query, included_pdfs)

    # Reranking processing
    rerank_results = []
    if search_results and len(search_results) > 0:
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
