import os
import sys
from pymilvus import MilvusClient
import ast

# Add the parent directory to sys.path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import chunk, convert
from utils.colored_logger import get_colored_logger

from config import Config
from rag_modules import get_database, insert, query

logger = get_colored_logger(__name__)

def get_pdf_names():
    """
    Fetches all PDF names from the Milvus database.
    
    Returns:
        set: A set of PDF names.
    """
    logger.info("Fetching PDF names from the database...")
    client = MilvusClient(uri=Config.DATABASE.path)
    results = client.query(  
        collection_name=Config.DATABASE.collection_name,  
        filter="id >= 0",  # matches all records since auto_id starts from 0  
        output_fields=["pdf_name"],  
    )  
    
    logger.info(f"Fetched {len(results)} results from the database.")
    pdf_names_set = set(result["pdf_name"] for result in results)
    return pdf_names_set

def insert_pdf(pdf_path: str):

    output_dir = os.path.dirname(pdf_path) + "/"
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    logger.info(f"Converting PDF: {pdf_path}, with output directory: {output_dir}")
    convert.pdf2md(pdf_path=pdf_path, output_dir=output_dir)

    logger.info(f"Converted files saved to {output_dir}")

    markdown_file = os.path.join(output_dir, f"{pdf_name}.md")
    metadata_file = os.path.join(output_dir, f"{pdf_name}_meta.json")
    
    if not os.path.exists(markdown_file) or not os.path.exists(metadata_file):
        logger.error(f"Conversion failed. Missing files: {markdown_file} or {metadata_file}")
        return False

    chunk_res = chunk.load_and_chunk(markdown_file, metadata_file)

    client = get_database.get_database_client()

    logger.info(f"Collection list: {client.list_collections()}")
    logger.info(f"Collection stats: {client.get_collection_stats(collection_name=Config.DATABASE.collection_name)}")

    success = insert.insert_data(chunk_res, pdf_name)
    if success:
        logger.info(f"Successfully inserted PDF: {pdf_name}")
        return True
    else:
        logger.error(f"Failed to insert PDF: {pdf_name}")
        return False


def set_active_pdfs(pdf_names: list):
    """
    Sets which PDFs should be currently used for querying.
    This is stored in memory for this session or can be persisted.
    
    Args:
        pdf_names: List of PDF names to set as active
    
    Returns:
        bool: True if successful
    """
    try:
        # For now, we'll use a simple approach where the caller manages this
        # In a real implementation, this could be stored in a session or config file
        logger.info(f"Set active PDFs: {pdf_names}")
        return True
    except Exception as e:
        logger.error(f"Error setting active PDFs: {e}")
        return False


async def query_pdfs_async(question: str, active_pdf_names: list):
    """
    Async version of query_pdfs for use with FastAPI.
    
    Args:
        question: User's question
        active_pdf_names: List of currently active PDF names
    
    Returns:
        str: Generated answer
    """
    try:
        from rag_modules.search import search_async
        from rag_modules import reranker, refer
        from rag_modules.query import split_query, generate_answer
        
        logger.info(f"Querying: '{question}' using PDFs: {active_pdf_names}")

        split_query = ast.literal_eval(query.split_query(question))
        split_query.insert(0, question)  # Ensure the original question is included

        logger.info(f"Split Query Success: {split_query}")

        
        
        # Get references and rerank
        references = refer.get_reference(split_query=split_query, included_pdfs=active_pdf_names)
        
        # Generate final answer
        answer = generate_answer(split_query, references)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error querying PDFs: {e}")
        return f"Error occurred while processing your query: {e}"


def query_pdfs(question: str, active_pdf_names: list):
    """
    Answers user's question based on the selected PDF(s).
    
    Args:
        question: User's question
        active_pdf_names: List of currently active PDF names
    
    Returns:
        str: Generated answer
    """
    try:
        from rag_modules import search, reranker, refer
        from rag_modules.query import split_query, generate_answer
        
        logger.info(f"Querying: '{question}' using PDFs: {active_pdf_names}")

        split_query = ast.literal_eval(query.split_query(question))
        split_query.insert(0, question)  # Ensure the original question is included

        logger.info(f"Split Query Success: {split_query}")

        
        
        # Get references and rerank
        references = refer.get_reference(split_query=split_query, included_pdfs=active_pdf_names)
        
        # Generate final answer
        answer = generate_answer(split_query, references)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error querying PDFs: {e}")
        return f"Error occurred while processing your query: {e}"


if __name__ == "__main__":
    print(get_pdf_names())
    # Get the absolute path to ensure it works regardless of where the script is run from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    pdf_path = os.path.join(project_root, "docs", "74HC165D.pdf")
    insert_pdf(pdf_path)
    