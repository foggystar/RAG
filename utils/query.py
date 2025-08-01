import os
import sys
from typing import List, Optional, Dict, Any

# 设置彩色日志
from .colored_logger import get_colored_logger
logger = get_colored_logger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_modules import refer
from api_client import ChatClient
from config import Config, ModelType


def split_query(
    query: List[str],
    api_key: Optional[str] = None
) -> List[str]:
    """
    Split a complex query into 2-3 sub-questions
    
    Args:
        query: The query to split
        api_key: Optional API key, will use config default if not provided
        
    Returns:
        List of sub-questions
    """
    try:
        client = ChatClient(api_key, ModelType.SPLIT)
        
        # Convert list to string if needed
        query_text = " ".join(query) if isinstance(query, list) else query
        
        messages = [
            {
                "role": "system", 
                "content": "Split the query into 2-3 sub-questions. Output only the questions, one per line."
            },
            {"role": "user", "content": query_text}
        ]
    
        content = client.create_completion(messages)
        
        if content:
            questions = [line.strip() for line in content.split('\n') if line.strip()]
            return query+questions if questions else query
        return query
    
    except Exception as e:
        logger.warning(f"Failed to split query: {e}")
        return query


def query_to_database(question: str, pdfs: List[str]) -> List[Dict[str, Any]]:
    """
    Query the database for relevant documents
    
    Args:
        question: The question to search for
        pdfs: List of PDF names to include in search
        
    Returns:
        List of relevant documents
    """
    results = refer.get_reference_with_filter(
        question, 
        included_pdfs=pdfs, 
        limit=Config.DEFAULT_SEARCH_LIMIT
    )
    return results if results else []


def generate_answer(
    questions: List[str],
    reference: List[Dict[str, Any]],
    api_key: Optional[str] = None,
    language: str = "chinese"
) -> str:
    """
    Generate an answer based on questions and reference documents
    
    Args:
        questions: List of questions to answer
        reference: List of reference documents
        api_key: Optional API key, will use config default if not provided
        language: Language for the response ("chinese" or "english")
        
    Returns:
        Generated answer
    """
    try:
        client = ChatClient(api_key, ModelType.CHAT)
        
        
        # Set system prompt based on language
        if language.lower() == "chinese":
            system_prompt = "You are a helpful assistant that answers questions based on the provided context. Provide page numbers of the context in your answer. You need to answer as detailed as possible and be consistant with the given context. Use Chinese to answer."
        else:
            system_prompt = "You are a helpful assistant that answers questions based on the provided context. Include page numbers from the context in your answer."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Questions:\n{questions}\n\nContext:\n{reference}"}
        ]

        logger.info("Starting answer generation...")
        content = client.create_completion(messages)
        return content if content else "No answer generated."
    
    except Exception as e:
        logger.warning(f"Failed to generate answer: {e}")
        return "Failed to generate answer due to an error."

