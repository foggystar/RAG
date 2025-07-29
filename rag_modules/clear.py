from pymilvus import MilvusClient

def clear_data(database: str = "milvus_rag.db", collection_name: str = "demo_collection"):
    """清除Milvus集合中的数据"""
    
    # 创建Milvus客户端
    client = MilvusClient(database)
    
    # 检查集合是否存在
    if not client.has_collection(collection_name=collection_name):
        print(f"集合 {collection_name} 不存在，无法清除数据")
        return
    
    # 清除集合中的所有数据
    client.drop_collection(collection_name=collection_name)

    
    print(f"集合 {collection_name} 中的数据已被清除")
