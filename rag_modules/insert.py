from typing import List
from pymilvus import MilvusClient
from .embedding import get_embedding, get_batch_embeddings_large_scale


def insert_data(texts: List[str], database: str = "milvus_rag.db", collection_name: str = "demo_collection"):
    """插入数据到Milvus集合"""
    
    # 创建Milvus客户端
    client = MilvusClient(database)
    
    # 检查集合是否存在
    if not client.has_collection(collection_name=collection_name):
        print(f"创建集合: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            dimension=768,  # 向量维度
        )
        
    
    embeddings = get_batch_embeddings_large_scale(texts)
    
    data = [
        {"id": i, "vector": embeddings[i], "text": texts[i], "subject": "history"}
        for i in range(len(embeddings))
    ]
    
    # 插入数据
    res = client.insert(collection_name="demo_collection", data=data)
    
    print(res)