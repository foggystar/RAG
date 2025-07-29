#!/usr/bin/env python3
"""
元数据过滤功能示例脚本
演示如何使用新的Milvus Collection schema进行PDF文档的屏蔽和过滤
"""

from rag_modules.insert import create_rag_collection, insert_data_with_metadata
from rag_modules.search import search_with_metadata_filter, search_only_unblocked
from rag_modules.refer import get_reference_with_filter
from pymilvus import MilvusClient


def main():
    """主函数：演示元数据过滤功能"""
    
    print("=== 元数据过滤功能演示 ===\n")
    
    collection_name = "rag_docs_demo"
    database = "milvus_rag.db"
    
    # 1. 创建Milvus客户端
    print("1. 创建Milvus客户端...")
    try:
        client = MilvusClient(database)
        print("✓ 客户端创建成功\n")
    except Exception as e:
        print(f"✗ 客户端创建失败: {e}")
        return
    
    # 2. 删除已存在的集合（如果有）
    if client.has_collection(collection_name):
        print(f"2. 删除已存在的集合 '{collection_name}'...")
        client.drop_collection(collection_name)
        print("✓ 删除成功\n")
    
    # 3. 准备示例数据
    print("3. 准备示例数据...")
    texts = [
        "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
        "机器学习是人工智能的一个分支，专门研究计算机怎样模拟或实现人类的学习行为，以获取新的知识或技能。",
        "深度学习是机器学习研究中的一个新的领域，其动机在于建立、模拟人脑进行分析学习的神经网络。",
        "自然语言处理是人工智能的一个重要分支，研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。",
        "计算机视觉是一门研究如何使机器'看'的科学，更进一步的说，就是是指用摄影机和电脑代替人眼对目标进行识别、跟踪和测量等机器视觉。"
    ]
    
    pdf_names = [
        "AI基础教程.pdf",
        "机器学习指南.pdf", 
        "深度学习详解.pdf",
        "NLP实战.pdf",
        "计算机视觉入门.pdf"
    ]
    
    page_numbers = [1, 1, 1, 1, 1]
    is_blocked_list = [False, False, True, False, False]  # 深度学习详解.pdf 被屏蔽
    
    # 4. 插入数据
    print("4. 插入带有元数据的数据...")
    try:
        insert_data_with_metadata(
            texts=texts,
            pdf_names=pdf_names,
            page_numbers=page_numbers,
            is_blocked_list=is_blocked_list,
            database=database,
            collection_name=collection_name
        )
        print("✓ 数据插入成功\n")
    except Exception as e:
        print(f"✗ 数据插入失败: {e}")
        return
    
    # 5. 测试搜索功能
    print("5. 测试搜索功能...")
    query = "什么是人工智能"
    
    # 5.1 普通搜索（无过滤）
    print("\n5.1 普通搜索（无过滤）:")
    try:
        results = search_with_metadata_filter([query], collection_name, limit=5, database=database)
        for i, result in enumerate(results[0]):
            entity = result['entity']
            print(f"  结果{i+1}: {entity['pdf_name']} - 屏蔽状态: {entity['is_blocked']}")
            print(f"    内容: {entity['text_content'][:50]}...")
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
    
    # 5.2 只搜索未被屏蔽的文档
    print("\n5.2 只搜索未被屏蔽的文档:")
    try:
        results = search_only_unblocked([query], collection_name, limit=5, database=database)
        for i, result in enumerate(results[0]):
            entity = result['entity']
            print(f"  结果{i+1}: {entity['pdf_name']} - 屏蔽状态: {entity['is_blocked']}")
            print(f"    内容: {entity['text_content'][:50]}...")
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
    
    # 5.3 排除特定PDF
    print("\n5.3 排除特定PDF（排除 'NLP实战.pdf'）:")
    try:
        # 使用过滤表达式排除特定PDF
        expr = "pdf_name != 'NLP实战.pdf'"
        results = search_with_metadata_filter([query], collection_name, limit=5, expr=expr, database=database)
        for i, result in enumerate(results[0]):
            entity = result['entity']
            print(f"  结果{i+1}: {entity['pdf_name']} - 屏蔽状态: {entity['is_blocked']}")
            print(f"    内容: {entity['text_content'][:50]}...")
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
    
    # 5.4 复合过滤（排除被屏蔽的文档和特定PDF）
    print("\n5.4 复合过滤（排除被屏蔽的文档和 'AI基础教程.pdf'）:")
    try:
        results = get_reference_with_filter(
            query=query,
            collection_name=collection_name,
            excluded_pdfs=["AI基础教程.pdf"],
            only_unblocked=True,
            database=database
        )
        for result in results:
            print(f"  序号{result['index']}: {result['pdf_name']} - 相关度: {result['relevance_score']:.3f}")
            print(f"    内容: {result['text'][:50]}...")
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
