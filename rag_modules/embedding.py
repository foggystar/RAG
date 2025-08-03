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


async def get_embedding_async(
    text: List[str]
) -> List[List[float]]:
    """Async version for use with FastAPI"""

    async def create_single_embedding_with_monitoring(client, text_item, index):
        """创建单个embedding并监控执行"""
        start_time = time.time()
        
        logger.info(f"Embedding text with length {len(text_item)}")
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
        
    return await create_embeddings_async()


def get_embedding(
    text: List[str]
) -> List[List[float]]:
    """Sync wrapper for backward compatibility"""
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # If we're in an event loop, we need to use a different approach
        # Create a new thread to run the async function
        import concurrent.futures
        
        def run_in_thread():
            # Create a new event loop in this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result = new_loop.run_until_complete(get_embedding_async(text))
                return result
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()
            
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(get_embedding_async(text))
