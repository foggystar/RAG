from pymilvus import MilvusClient

from config import Config
from utils.colored_logger import get_colored_logger

logger = get_colored_logger(__name__)

def clear_database():
    """清除Milvus集合中的数据"""
    
    # 创建Milvus客户端
    client = MilvusClient(Config.DATABASE.path)
    
    # 检查集合是否存在
    if not client.has_collection(collection_name=Config.DATABASE.collection_name):
        logger.warning(f"集合 {Config.DATABASE.collection_name} 不存在，无法清除数据")
        return
    
    # 清除集合中的所有数据
    client.drop_collection(collection_name=Config.DATABASE.collection_name)    
    logger.info(f"集合 {Config.DATABASE.collection_name} 中的数据已被清除")

    