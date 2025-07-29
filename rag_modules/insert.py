from typing import List, Optional
from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType, Collection, connections
from .embedding import get_embedding, get_batch_embeddings_large_scale


def create_rag_collection(collection_name: str = "rag_docs"):
    """创建带有元数据字段的RAG集合"""
    
    # 定义集合schema
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768),  # 向量维度
        FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=65535),  # 存储原始文本片段
        FieldSchema(name="pdf_name", dtype=DataType.VARCHAR, max_length=256),  # PDF文件名
        FieldSchema(name="page_number", dtype=DataType.INT64),  # 页码
        FieldSchema(name="is_blocked", dtype=DataType.BOOL)  # 是否被屏蔽的标志
    ]
    
    schema = CollectionSchema(fields, "Collection for RAG documents")
    collection = Collection(collection_name, schema)
    
    # 创建索引
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 1024}
    }
    collection.create_index(field_name="vector", index_params=index_params)
    
    print(f"创建集合 '{collection_name}' 成功")
    return collection


def insert_data_with_metadata(
    texts: List[str], 
    pdf_names: List[str],
    page_numbers: List[int],
    is_blocked_list: Optional[List[bool]] = None,
    database: str = "milvus_rag.db", 
    collection_name: str = "rag_docs"
):
    """插入带有元数据的数据到Milvus集合"""
    
    if is_blocked_list is None:
        is_blocked_list = [False] * len(texts)
    
    # 验证输入长度一致性
    if not (len(texts) == len(pdf_names) == len(page_numbers) == len(is_blocked_list)):
        raise ValueError("所有输入列表长度必须一致")
    
    # 创建Milvus客户端（使用Lite版本保持一致性）
    client = MilvusClient(database)
    
    # 检查集合是否存在，不存在则创建带有元数据的集合
    if not client.has_collection(collection_name=collection_name):
        print(f"集合 '{collection_name}' 不存在，创建新集合...")
        # 为MilvusClient创建带有元数据的集合
        client.create_collection(
            collection_name=collection_name,
            dimension=768,  # 向量维度
            id_type="int",
            primary_field_name="id",
            vector_field_name="vector"
        )
    
    # 获取embedding向量
    embeddings = get_batch_embeddings_large_scale(texts)
    
    # 准备数据 - 适配MilvusClient格式
    data = []
    for i in range(len(texts)):
        data.append({
            "id": i,
            "vector": embeddings[i],
            "text_content": texts[i],
            "pdf_name": pdf_names[i],
            "page_number": page_numbers[i],
            "is_blocked": is_blocked_list[i]
        })
    
    # 插入数据
    res = client.insert(collection_name=collection_name, data=data)
    
    print(f"成功插入 {len(texts)} 条记录到集合 '{collection_name}'")
    return res


# def insert_data(texts: List[str], database: str = "milvus_rag.db", collection_name: str = "demo_collection"):
#     """插入数据到Milvus集合 (保持向后兼容性)"""
    
#     # 创建Milvus客户端
#     client = MilvusClient(database)
    
#     # 检查集合是否存在
#     if not client.has_collection(collection_name=collection_name):
#         print(f"创建集合: {collection_name}")
#         client.create_collection(
#             collection_name=collection_name,
#             dimension=768,  # 向量维度
#         )
        
    
#     embeddings = get_batch_embeddings_large_scale(texts)
    
#     data = [
#         {"id": i, "vector": embeddings[i], "text": texts[i], "subject": "history"}
#         for i in range(len(embeddings))
#     ]
    
#     # 插入数据
#     res = client.insert(collection_name=collection_name, data=data)
    
#     print(res)