import os
import sys
from typing import List, Optional, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_modules import refer
from api_client import ChatClient
from config import Config, ModelType
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)

def split_query(
    query: str
) -> List[str]:
    """
    Split a complex query into 2-3 sub-questions
    
    Args:
        query: The query to split
        
    Returns:
        List of sub-questions
    """
    logger.info(f"Splitting query: {query}")
    try:
        client = ChatClient(model_type=ModelType.SPLIT)
        
        messages = [
            {
                "role": "system", 
                "content": "Split the query into 3-4 sub-questions. Output only the questions, with python list format."
            },
            {"role": "user", "content": query}
        ]
    
        content = client.create_completion(messages)
 
        return content

    except Exception as e:
        logger.warning(f"Failed to split query: {e}")
        return query

def generate_answer(
    questions: List[str],
    reference: List[str],
    language: str = "chinese"
) -> str:
    """
    Generate an answer based on questions and reference documents
    
    Args:
        questions: List of questions to answer
        reference: List of reference documents
        language: Language for the response ("chinese" or "english")
        
    Returns:
        Generated answer
    """
    try:
        client = ChatClient(model_type=ModelType.CHAT)
        
        user_prompt = f"Questions: {questions}\n References: {reference}\n"
        
        # Set system prompt based on language
        if language.lower() == "chinese":
            system_prompt = "You are a helpful assistant that answers questions in detail, based on the provided context. Provide page numbers of the context in your answer. You need to answer as detailed as possible and be consistant with the given context. Use Chinese to answer. You need to use markdown format to answer, if you need to use pictures in the reference, copy the image link to the answer as a markdown link format, because the image file will be put besides your response, do not modify any thing about the link."
        else:
            system_prompt = "You are a helpful assistant that answers questions in detail, based on the provided context. Provide page numbers of the context in your answer. You need to answer as detailed as possible and be consistant with the given context. Use Englist to answer. You need to use markdown format to answer, if you need to use pictures in the reference, copy the image link to the answer."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        logger.info("Starting answer generation...")
        content = client.create_completion(messages)
        return content if content else "No answer generated."
    
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        return "Failed to generate answer due to an error."

if __name__ == "__main__":
    # Example usage
    query = "hello"
 
    answer = generate_answer([query], [query])
    logger.info(f"Generated Answer: {answer}")
