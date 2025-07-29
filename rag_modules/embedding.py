import os
import asyncio
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
    
    Raises:
        Exception: 当API调用失败时抛出异常
    """
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable or pass api_key parameter.")
    
    # 创建OpenAI客户端，指向SiliconFlow的API端点
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
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable or pass api_key parameter.")
    
    # 创建OpenAI客户端
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

def get_batch_embeddings_optimized(
    texts: List[str],
    model: str = "Qwen/Qwen3-Embedding-4B",
    dimensions: int = 768,
    api_key: Optional[str] = None,
    max_workers: int = 3,
    min_batch_size: int = 50  # 增大最小批次大小
) -> List[List[float]]:
    """
    优化的并发批量获取embedding向量
    
    Args:
        texts: 文本列表
        model: 使用的模型名称
        dimensions: 向量维度
        api_key: API密钥
        max_workers: 最大并发线程数
        min_batch_size: 最小批次大小，小于此值直接串行处理
    
    Returns:
        embedding向量列表的列表
    """
    if not texts:
        return []
    
    # 小数据集直接使用原始方法，避免并发开销
    if len(texts) <= min_batch_size:
        return get_batch_embeddings(texts, model, dimensions, api_key)
    
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable or pass api_key parameter.")
    
    # 动态计算最优批次大小
    total_texts = len(texts)
    # 每个线程处理的理想文本数量
    optimal_batch_size = max(min_batch_size, total_texts // max_workers)
    # 确保批次数量不会太多
    actual_batch_size = min(optimal_batch_size, 100)  # 最大批次100个文本
    
    def process_batch(batch_texts: List[str], batch_index: int) -> tuple[int, List[List[float]]]:
        """处理单个批次的文本"""
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
        try:
            response = client.embeddings.create(
                model=model,
                input=batch_texts,
                encoding_format="float",
                dimensions=dimensions
            )
            embeddings = [data.embedding for data in response.data]
            return batch_index, embeddings
        except Exception as e:
            raise Exception(f"Batch {batch_index} API request failed: {e}")
    
    # 将文本分批 - 使用动态批次大小
    text_batches = []
    for i in range(0, len(texts), actual_batch_size):
        batch = texts[i:i + actual_batch_size]
        text_batches.append((batch, i // actual_batch_size))
    
    # 如果只有一个批次，直接使用原始方法
    if len(text_batches) == 1:
        return get_batch_embeddings(texts, model, dimensions, api_key)
    
    # 使用线程池并发处理
    results = {}
    with ThreadPoolExecutor(max_workers=min(max_workers, len(text_batches))) as executor:
        # 提交所有批次任务
        future_to_batch = {
            executor.submit(process_batch, batch_texts, batch_index): batch_index
            for batch_texts, batch_index in text_batches
        }
        
        # 收集结果
        for future in as_completed(future_to_batch):
            try:
                batch_index, batch_embeddings = future.result()
                results[batch_index] = batch_embeddings
            except Exception as e:
                raise Exception(f"Failed to process batch: {e}")
    
    # 按原始顺序重新组织结果
    final_embeddings = []
    for i in range(len(text_batches)):
        final_embeddings.extend(results[i])
    
    return final_embeddings

def get_batch_embeddings_large_scale(
    texts: List[str],
    model: str = "Qwen/Qwen3-Embedding-4B",
    dimensions: int = 768,
    api_key: Optional[str] = None,
    max_workers: int = 4,
    texts_per_worker: int = 200  # 每个工作线程处理的文本数量
) -> List[List[float]]:
    """
    大规模并发批量获取embedding向量 - 适用于数百到数千个文本
    只有在文本数量超过阈值时才使用并发，避免小数据集的开销
    
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
    
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found.")
    
    def process_chunk(chunk_texts: List[str], chunk_index: int) -> tuple[int, List[List[float]]]:
        """处理一个大块的文本 - 每个线程内部使用高效的原始批量方法"""
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

async def get_batch_embeddings_async(
    texts: List[str],
    model: str = "Qwen/Qwen3-Embedding-4B",
    dimensions: int = 768,
    api_key: Optional[str] = None,
    max_concurrent: int = 5,
    batch_size: int = 20
) -> List[List[float]]:
    """
    异步批量获取多个文本的embedding向量
    
    Args:
        texts: 文本列表
        model: 使用的模型名称
        dimensions: 向量维度
        api_key: API密钥
        max_concurrent: 最大并发数
        batch_size: 每批处理的文本数量
    
    Returns:
        embedding向量列表的列表
    """
    if not texts:
        return []
    
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable or pass api_key parameter.")
    
    async def process_batch_async(batch_texts: List[str], batch_index: int) -> tuple[int, List[List[float]]]:
        """异步处理单个批次的文本"""
        # 在异步函数中使用同步的OpenAI客户端
        loop = asyncio.get_event_loop()
        
        def sync_request():
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            response = client.embeddings.create(
                model=model,
                input=batch_texts,
                encoding_format="float",
                dimensions=dimensions
            )
            return [data.embedding for data in response.data]
        
        try:
            embeddings = await loop.run_in_executor(None, sync_request)
            return batch_index, embeddings
        except Exception as e:
            raise Exception(f"Async batch {batch_index} API request failed: {e}")
    
    # 将文本分批
    text_batches = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        text_batches.append((batch, i // batch_size))
    
    # 使用信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(batch_texts: List[str], batch_index: int):
        async with semaphore:
            return await process_batch_async(batch_texts, batch_index)
    
    # 并发处理所有批次
    tasks = [
        process_with_semaphore(batch_texts, batch_index)
        for batch_texts, batch_index in text_batches
    ]
    
    results = {}
    try:
        batch_results = await asyncio.gather(*tasks)
        for batch_index, batch_embeddings in batch_results:
            results[batch_index] = batch_embeddings
    except Exception as e:
        raise Exception(f"Failed to process batches asynchronously: {e}")
    
    # 按原始顺序重新组织结果
    final_embeddings = []
    for i in range(len(text_batches)):
        final_embeddings.extend(results[i])
    
    return final_embeddings

# 示例用法
if __name__ == "__main__":
    import time
    
    # 单个文本embedding
    text = "Silicon flow embedding online: fast, affordable, and high-quality embedding services. come try it out!"
    embedding = get_embedding(text)
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    
    # 准备测试数据
    texts = [
        "Hello world",
        "Python programming", 
        "Machine learning",
        "Deep learning algorithms",
        "Natural language processing",
        "Computer vision applications",
        "Data science workflows",
        "Artificial intelligence systems",
        "Neural network architectures",
        "Transformer models"
    ] * 5  # 创建50个文本用于测试并发性能
    
    print(f"\n测试数据: {len(texts)} 个文本")
    
    # 测试原始批量处理
    print("\n--- 原始批量处理 ---")
    start_time = time.time()
    batch_embeddings = get_batch_embeddings(texts)
    original_time = time.time() - start_time
    print(f"原始方法耗时: {original_time:.2f} 秒")
    print(f"处理了 {len(batch_embeddings)} 个文本")
    
    # 测试并发批量处理
    print("\n--- 优化的并发批量处理 ---")
    start_time = time.time()
    optimized_embeddings = get_batch_embeddings_optimized(
        texts, 
        max_workers=3
    )
    optimized_time = time.time() - start_time
    print(f"优化并发方法耗时: {optimized_time:.2f} 秒")
    print(f"处理了 {len(optimized_embeddings)} 个文本")
    print(f"性能提升: {original_time/optimized_time:.2f}x")
    
    # 测试大规模并发处理
    print("\n--- 大规模并发批量处理 ---")
    start_time = time.time()
    large_scale_embeddings = get_batch_embeddings_large_scale(
        texts, 
        max_workers=3,
        texts_per_worker=100  # 降低阈值用于演示
    )
    large_scale_time = time.time() - start_time
    print(f"大规模并发方法耗时: {large_scale_time:.2f} 秒")
    print(f"处理了 {len(large_scale_embeddings)} 个文本")
    print(f"性能提升: {original_time/large_scale_time:.2f}x")
    
    # 测试异步批量处理
    print("\n--- 异步批量处理 ---")
    async def test_async():
        start_time = time.time()
        async_embeddings = await get_batch_embeddings_async(
            texts[:20],  # 使用较少文本进行异步测试
            max_concurrent=3,
            batch_size=5
        )
        async_time = time.time() - start_time
        print(f"异步方法耗时: {async_time:.2f} 秒")
        print(f"处理了 {len(async_embeddings)} 个文本")
        return async_embeddings
    
    # 运行异步测试
    async_embeddings = asyncio.run(test_async())
    
    # 验证结果一致性
    print("\n--- 结果验证 ---")
    print(f"原始方法维度: {len(batch_embeddings[0])}")
    print(f"优化并发方法维度: {len(optimized_embeddings[0])}")
    print(f"大规模并发方法维度: {len(large_scale_embeddings[0])}")
    print(f"异步方法维度: {len(async_embeddings[0])}")
    
    # 比较前几个向量的一致性
    print("前3个文本的embedding是否一致:")
    for i in range(min(3, len(texts))):
        original = batch_embeddings[i][:5]
        optimized = optimized_embeddings[i][:5]
        print(f"文本 {i+1}: 原始={original}, 优化并发={optimized}")
        print(f"  一致性: {original == optimized}")