from pymilvus import MilvusClient
import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置彩色日志
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)

def clear_data(database: str = "milvus_rag.db", collection_name: str = "demo_collection"):
    """清除Milvus集合中的数据"""
    
    # 创建Milvus客户端
    client = MilvusClient(database)
    
    # 检查集合是否存在
    if not client.has_collection(collection_name=collection_name):
        logger.warning(f"集合 {collection_name} 不存在，无法清除数据")
        return
    
    # 清除集合中的所有数据
    client.drop_collection(collection_name=collection_name)

    
    logger.info(f"集合 {collection_name} 中的数据已被清除")
