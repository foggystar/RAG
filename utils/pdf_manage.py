import os
import sys
from pymilvus import MilvusClient

# Add the parent directory to sys.path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import chunk, convert
from utils.colored_logger import get_colored_logger

from config import Config
from rag_modules import get_database, insert

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

    # chunk_res = chunk.load_and_chunk(f"{pdf_name}.md",f"{pdf_name}_meta.json")

    # client = get_database.get_database_client()

    # logger.info(f"Collection list: {client.list_collections()}")
    # logger.info(f"Collection stats: {client.get_collection_stats(collection_name=Config.DATABASE.collection_name)}")

    # insert.insert_data(chunk_res, f"{pdf_name}")


if __name__ == "__main__":
    print(get_pdf_names())
    # Get the absolute path to ensure it works regardless of where the script is run from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    pdf_path = os.path.join(project_root, "docs", "74HC165D.pdf")
    insert_pdf(pdf_path)
    