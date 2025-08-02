from pymilvus import MilvusClient, DataType
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置彩色日志
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)

from config import DatabaseConfig

def get_database_client() -> MilvusClient:
    
    client = MilvusClient(uri=DatabaseConfig.path)
    index_params = MilvusClient.prepare_index_params()

    # Check if collection exists, create with metadata if it doesn't
    if not client.has_collection(collection_name=DatabaseConfig.collection_name):
        logger.info(f"Collection '{DatabaseConfig.collection_name}' does not exist, creating new collection...")

        schema = MilvusClient.create_schema()

        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=DatabaseConfig.dimensions)
        schema.add_field(field_name="text_content", datatype=DataType.VARCHAR, max_length=DatabaseConfig.chunk_size_limit+100)
        schema.add_field(field_name="pdf_name", datatype=DataType.VARCHAR, max_length=100)
        schema.add_field(field_name="page_number", datatype=DataType.INT16)

        client.create_collection(collection_name=DatabaseConfig.collection_name, schema=schema)

        logger.info("Creating vector index...")
        index_params.add_index(
            field_name="vector", # Name of the vector field to be indexed
            index_type="IVF_FLAT", # Type of the index to create
            index_name="vector", # Name of the index to create
            metric_type="COSINE", # Metric type used to measure similarity
            params={
                "nlist": 1024, # Number of clusters for the index
                "nprobe": 128, # Number of clusters to search
            } # Index building params
        )

        client.create_index(
            collection_name=DatabaseConfig.collection_name,
            index_params=index_params
        )

        

        logger.info(f"Collection '{DatabaseConfig.collection_name}' created successfully")
    
    return client