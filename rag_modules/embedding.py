from typing import List
import sys
import os
import asyncio
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import EmbeddingClient
from config import Config
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)


def get_embedding(
    text: List[str]
) -> List[List[float]]:

    async def create_single_embedding_with_monitoring(client, text_item, index):
        """创建单个embedding并监控执行"""
        start_time = time.time()
        
        try:
            result = await client.create_embedding_async(text_item)
            duration = time.time() - start_time
            logger.info(f"[{index + 1}] {duration:.2f}s ")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{index + 1}] ✗ {duration:.2f}s | 错误: {str(e)}")
            raise

    async def create_embeddings_async():
        client = EmbeddingClient(Config.get_api_key())
        logger.info(f"处理 {len(text)} 个文本...")
        
        tasks = [
            create_single_embedding_with_monitoring(client, t, i) 
            for i, t in enumerate(text)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        logger.info(f"完成! 总耗时: {total_time:.2f}s | 平均: {total_time/len(text):.2f}s")
        return results
        
    return asyncio.run(create_embeddings_async())
