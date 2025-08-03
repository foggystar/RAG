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

async def insert_pdf(pdf_path: str):

    output_dir = os.path.dirname(pdf_path) + "/"
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    logger.info(f"Converting PDF: {pdf_path}, with output directory: {output_dir}")
    convert.pdf2md(pdf_path=pdf_path, output_dir=output_dir)

    logger.info(f"Converted files saved to {output_dir}")

    markdown_file = os.path.join(output_dir, f"{pdf_name}/{pdf_name}.md")
    metadata_file = os.path.join(output_dir, f"{pdf_name}/{pdf_name}_meta.json")
    
    if not os.path.exists(markdown_file) or not os.path.exists(metadata_file):
        logger.error(f"Conversion failed. Missing files: {markdown_file} or {metadata_file}")
        return False

    chunk_res = chunk.load_and_chunk(markdown_file, metadata_file)

    client = get_database.get_database_client()

    logger.info(f"Collection list: {client.list_collections()}")
    logger.info(f"Collection stats: {client.get_collection_stats(collection_name=Config.DATABASE.collection_name)}")
    # print(chunk_res)

    success = await insert.insert_data(chunk_res, pdf_name)
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

        split_queries = ast.literal_eval(query.split_query(question))
        split_queries.insert(0, question)  # Ensure the original question is included

        logger.info(f"Split Query Success: {split_queries}")

        # Get references and rerank (async)
        references = await refer.get_reference(split_query=split_queries, included_pdfs=active_pdf_names)
        
        # Generate final answer
        answer = generate_answer(split_queries, references)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error querying PDFs: {e}")
        return f"Error occurred while processing your query: {e}"


async def query_pdfs_stream_async(question: str, active_pdf_names: list):
    """
    Streaming async version of query_pdfs for use with FastAPI.
    
    Args:
        question: User's question
        active_pdf_names: List of currently active PDF names
    
    Yields:
        str: Chunks of generated answer
    """
    try:
        from rag_modules.search import search_async
        from rag_modules import reranker, refer
        from rag_modules.query import split_query, generate_answer_stream
        
        logger.info(f"Streaming query: '{question}' using PDFs: {active_pdf_names}")

        # Split query (this can be blocking, but it's usually fast)
        split_queries = ast.literal_eval(query.split_query(question))
        split_queries.insert(0, question)  # Ensure the original question is included

        logger.info(f"Split Query Success: {split_queries}")
        
        # Get references and rerank (async) - this is the potentially slow part
        references = await refer.get_reference(split_query=split_queries, included_pdfs=active_pdf_names)
        logger.info(f"Retrieved {len(references)} references")
        
        # Generate streaming answer - this should be truly streaming
        chunk_count = 0
        for chunk in generate_answer_stream(split_queries, references):
            if chunk:
                chunk_count += 1
                logger.debug(f"Yielding chunk {chunk_count}: {chunk[:50]}...")
                yield chunk
                # Add small delay to ensure true streaming behavior
                import asyncio
                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
        
        logger.info(f"Streaming completed with {chunk_count} chunks")
        
    except Exception as e:
        logger.error(f"Error in streaming query: {e}")
        yield f"Error occurred while processing your query: {e}"


def delete_pdf(pdf_name: str):
    """
    Deletes a specific PDF and all its associated data from the Milvus database.
    
    Args:
        pdf_name: Name of the PDF to delete (without extension)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Attempting to delete PDF: {pdf_name}")
        
        # Create Milvus client
        client = MilvusClient(uri=Config.DATABASE.path)
        
        # Check if collection exists
        if not client.has_collection(collection_name=Config.DATABASE.collection_name):
            logger.warning(f"Collection {Config.DATABASE.collection_name} does not exist")
            return False
        
        # Check if PDF exists in database
        existing_pdfs = get_pdf_names()
        if pdf_name not in existing_pdfs:
            logger.warning(f"PDF '{pdf_name}' not found in database")
            return False
        
        # Delete all records associated with this PDF
        res = client.delete(
            collection_name=Config.DATABASE.collection_name,
            filter=f'pdf_name == "{pdf_name}"'
        )
        
        # Handle different response formats from Milvus
        delete_count = "unknown"
        if isinstance(res, dict):
            delete_count = res.get('delete_count', 'unknown')
        elif isinstance(res, list):
            delete_count = len(res)
        
        logger.info(f"Successfully deleted PDF '{pdf_name}' from database. Deleted {delete_count} records.")
        
        # Optionally, also delete the physical files
        try:
            import shutil
            # Delete from uploads directory
            upload_file = f"uploads/{pdf_name}.pdf"
            if os.path.exists(upload_file):
                os.remove(upload_file)
                logger.info(f"Deleted physical file: {upload_file}")
            
            # Delete from docs directory and its processed folder
            docs_folder = f"docs/{pdf_name}"
            if os.path.exists(docs_folder):
                shutil.rmtree(docs_folder)
                logger.info(f"Deleted processed folder: {docs_folder}")
                
            uploads_folder = f"uploads/{pdf_name}"
            if os.path.exists(uploads_folder):
                shutil.rmtree(uploads_folder)
                logger.info(f"Deleted uploads folder: {uploads_folder}")
                
        except Exception as file_error:
            logger.warning(f"Could not delete physical files for {pdf_name}: {file_error}")
            # Don't fail the operation if file deletion fails
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting PDF '{pdf_name}': {e}")
        return False


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

        split_queries = ast.literal_eval(query.split_query(question))
        split_queries.insert(0, question)  # Ensure the original question is included

        logger.info(f"Split Query Success: {split_queries}")

        # Get references and rerank (sync version)
        references = refer.get_reference_sync(split_query=split_queries, included_pdfs=active_pdf_names)
        
        # Generate final answer
        answer = generate_answer(split_queries, references)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error querying PDFs: {e}")
        return f"Error occurred while processing your query: {e}"


if __name__ == "__main__":
    import asyncio
    
    print(get_pdf_names())
    # Get the absolute path to ensure it works regardless of where the script is run from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    pdf_path = os.path.join(project_root, "docs", "74HC165D.pdf")
    asyncio.run(insert_pdf(pdf_path))
    