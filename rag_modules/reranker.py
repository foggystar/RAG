from typing import List, Optional, Dict, Any
import os
import requests


def get_rerank(
    query: str,
    documents: List[str],
    top_n: int = 5,
    model: str = "Qwen/Qwen3-Reranker-4B", 
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    批量获取文档重排序结果
    
    Args:
        query: 查询文本
        documents: 文档列表
        top_n: 返回前N个结果
        model: 使用的重排序模型名称
        api_key: API密钥
    
    Returns:
        重排序结果列表，包含文档索引和分数
    """
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable or pass api_key parameter.")
    
    # 准备请求数据
    url = "https://api.siliconflow.cn/v1/rerank"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": top_n
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return result.get('results', [])
        
    except requests.exceptions.HTTPError as e:
        # 尝试获取更详细的错误信息
        try:
            error_detail = response.json()
            raise Exception(f"Rerank API HTTP Error: {e}, Details: {error_detail}")
        except:
            raise Exception(f"Rerank API HTTP Error: {e}, Status Code: {response.status_code}")
    except Exception as e:
        raise Exception(f"Rerank API request failed: {e}")