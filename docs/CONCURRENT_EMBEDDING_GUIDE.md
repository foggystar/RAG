# 并发Embedding使用指南

## 概述

本项目提供了三种获取文本embedding的方法：

1. **串行方法** (`get_batch_embeddings`) - 原始实现，逐个处理文本
2. **并发方法** (`get_batch_embeddings_concurrent`) - 使用线程池并发处理
3. **异步方法** (`get_batch_embeddings_async`) - 使用异步编程模式

## 方法对比

### 1. 串行方法 `get_batch_embeddings`
```python
embeddings = get_batch_embeddings(texts)
```
- **适用场景**: 文本数量较少 (< 20个)
- **优点**: 简单可靠，内存占用低
- **缺点**: 处理大量文本时速度较慢

### 2. 并发方法 `get_batch_embeddings_concurrent`
```python
embeddings = get_batch_embeddings_concurrent(
    texts, 
    max_workers=5,      # 最大线程数
    batch_size=20       # 每批文本数量
)
```
- **适用场景**: 中等数量文本 (20-200个)
- **优点**: 显著提升处理速度，实现简单
- **缺点**: 线程开销，内存占用稍高

### 3. 异步方法 `get_batch_embeddings_async`
```python
embeddings = await get_batch_embeddings_async(
    texts,
    max_concurrent=5,   # 最大并发数
    batch_size=20       # 每批文本数量
)
```
- **适用场景**: 大量文本 (200+个) 或需要与其他异步代码集成
- **优点**: 高效的I/O处理，适合异步应用
- **缺点**: 代码复杂度较高，需要异步环境

## 参数调优建议

### 线程数/并发数设置
- **保守设置**: 3-5个线程/并发
- **激进设置**: 8-10个线程/并发
- **注意**: 过多线程可能导致API限流

### 批次大小设置
- **小文本** (< 100字符): batch_size = 50-100
- **中等文本** (100-500字符): batch_size = 20-50  
- **大文本** (> 500字符): batch_size = 5-20
- **API限制**: 每次请求不超过模型token限制

## 性能测试

运行性能测试脚本：
```bash
python test_concurrent_embedding.py
```

### 预期性能提升
- **10-50个文本**: 2-3x 速度提升
- **50-200个文本**: 3-5x 速度提升
- **200+个文本**: 5-8x 速度提升

## 最佳实践

### 1. 错误处理
```python
try:
    embeddings = get_batch_embeddings_concurrent(texts)
except Exception as e:
    # 降级到串行处理
    embeddings = get_batch_embeddings(texts)
```

### 2. 内存管理
```python
# 对于大量文本，分块处理
def process_large_dataset(texts, chunk_size=1000):
    results = []
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i+chunk_size]
        chunk_embeddings = get_batch_embeddings_concurrent(
            chunk, max_workers=3, batch_size=20
        )
        results.extend(chunk_embeddings)
    return results
```

### 3. API限流处理
```python
import time
import random

def get_embeddings_with_retry(texts, max_retries=3):
    for attempt in range(max_retries):
        try:
            return get_batch_embeddings_concurrent(
                texts, max_workers=3  # 保守的并发数
            )
        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise e
```

## 环境要求

```bash
# 安装依赖
pip install openai

# 设置API密钥
export siliconflow_api_key="your_api_key_here"
```

## 故障排除

### 常见问题

1. **API限流错误**
   - 减少 `max_workers` 参数
   - 增加批次间延迟
   - 实现指数退避重试

2. **内存不足**
   - 减少 `batch_size` 参数
   - 分块处理大数据集
   - 降低并发数

3. **连接超时**
   - 实现重试机制
   - 检查网络连接
   - 适当增加超时时间

### 性能调优步骤

1. **基准测试**: 先测试串行方法性能
2. **逐步增加并发**: 从2个线程开始，逐步增加
3. **监控API响应**: 注意错误率和响应时间
4. **调整批次大小**: 根据文本长度调整
5. **压力测试**: 模拟生产环境负载

## 示例代码

```python
import asyncio
from embedding import (
    get_batch_embeddings,
    get_batch_embeddings_concurrent,
    get_batch_embeddings_async
)

# 准备测试数据
texts = ["测试文本 " + str(i) for i in range(50)]

# 方法1: 串行处理
embeddings1 = get_batch_embeddings(texts)

# 方法2: 并发处理
embeddings2 = get_batch_embeddings_concurrent(
    texts, 
    max_workers=3, 
    batch_size=10
)

# 方法3: 异步处理  
async def main():
    embeddings3 = await get_batch_embeddings_async(
        texts,
        max_concurrent=3,
        batch_size=10
    )
    return embeddings3

embeddings3 = asyncio.run(main())
```
