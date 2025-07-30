import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from openai import OpenAI


def get_embedding(
    text: str, 
    model: str = "Qwen/Qwen3-Embedding-4B",
    dimensions: int = 768,
    api_key: Optional[str] = None
) -> List[float]:
    """
    获取文本的embedding向量
    
    Args:
        text: 要处理的文本
        model: 使用的模型名称
        dimensions: 向量维度
        api_key: API密钥, 如果不提供则从环境变量获取
    
    Returns:
        embedding向量列表
    """
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable.")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1"
    )
    
    try:
        response = client.embeddings.create(
            model=model,
            input=text,
            encoding_format="float",
            dimensions=dimensions
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"API request failed: {e}")


def get_batch_embeddings(
    texts: List[str],
    model: str = "Qwen/Qwen3-Embedding-4B", 
    dimensions: int = 768,
    api_key: Optional[str] = None
) -> List[List[float]]:
    """
    批量获取多个文本的embedding向量
    
    Args:
        texts: 文本列表
        model: 使用的模型名称
        dimensions: 向量维度
        api_key: API密钥
    
    Returns:
        embedding向量列表的列表
    """
    if not texts:
        return []
        
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable.")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1"
    )
    
    try:
        response = client.embeddings.create(
            model=model,
            input=texts,
            encoding_format="float",
            dimensions=dimensions
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        raise Exception(f"Batch API request failed: {e}")


def get_batch_embeddings_large_scale(
    texts: List[str],
    model: str = "Qwen/Qwen3-Embedding-4B",
    dimensions: int = 768,
    api_key: Optional[str] = None,
    max_workers: int = 3,
    texts_per_worker: int = 100
) -> List[List[float]]:
    """
    大规模并发批量获取embedding向量 - 适用于数百到数千个文本
    
    Args:
        texts: 文本列表
        model: 使用的模型名称  
        dimensions: 向量维度
        api_key: API密钥
        max_workers: 最大并发线程数
        texts_per_worker: 每个工作线程处理的文本数量
    
    Returns:
        embedding向量列表的列表
    """
    if not texts:
        return []
    
    # 小数据集直接使用原始方法，避免并发开销
    if len(texts) <= texts_per_worker:
        return get_batch_embeddings(texts, model, dimensions, api_key)
    
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found.")
    
    def process_chunk(chunk_texts: List[str], chunk_index: int) -> tuple[int, List[List[float]]]:
        """处理一个大块的文本"""
        return chunk_index, get_batch_embeddings(chunk_texts, model, dimensions, api_key)
    
    # 将文本按工作线程分块
    chunks = []
    for i in range(0, len(texts), texts_per_worker):
        chunk = texts[i:i + texts_per_worker]
        chunks.append((chunk, i // texts_per_worker))
    
    # 动态调整工作线程数
    actual_workers = min(max_workers, len(chunks))
    
    # 使用线程池处理大块
    results = {}
    with ThreadPoolExecutor(max_workers=actual_workers) as executor:
        future_to_chunk = {
            executor.submit(process_chunk, chunk_texts, chunk_index): chunk_index
            for chunk_texts, chunk_index in chunks
        }
        
        for future in as_completed(future_to_chunk):
            chunk_index, chunk_embeddings = future.result()
            results[chunk_index] = chunk_embeddings
    
    # 按原始顺序重新组织结果
    final_embeddings = []
    for i in range(len(chunks)):
        final_embeddings.extend(results[i])
    
    return final_embeddings