from rag_modules import insert, clear, refer
from rag_modules.pdf_manager import PDFManager


def demo_basic_functionality():
    """演示基础功能"""
    print("=== 基础功能演示 ===")
    
    docs = [
        "Newton's laws of motion form the foundation of classical mechanics.",
        "The periodic table organizes elements by their atomic number and properties.",
        "DNA carries genetic information in all living organisms.",
        "Photosynthesis converts sunlight into chemical energy in plants.",
        "Einstein's theory of relativity revolutionized our understanding of space and time.",
        "The mitochondria is known as the powerhouse of the cell.",
        "Quantum mechanics describes the behavior of matter at the atomic scale.",
        "The speed of light in vacuum is approximately 299,792,458 meters per second.",
        "Chemical bonds form when atoms share or transfer electrons.",
        "The human brain contains approximately 86 billion neurons.",
        "Thermodynamics governs energy transfer and transformation in physical systems.",
        "Evolution by natural selection explains the diversity of life on Earth.",
        "The electromagnetic spectrum includes radio waves, microwaves, and visible light.",
        "Protein synthesis occurs through transcription and translation processes.",
        "Mathematical calculus is essential for understanding rates of change.",
        "The structure of an atom consists of protons, neutrons, and electrons.",
        "Mendel's laws describe the inheritance patterns of genetic traits.",
        "The carbon cycle is crucial for maintaining Earth's climate balance.",
        "Semiconductor materials are fundamental to modern electronic devices.",
        "Antibiotics work by targeting specific bacterial cellular processes."
    ]

    # 将docs作为一个未被屏蔽的PDF处理
    clear.clear_data()  # 清除数据
    
    # 准备元数据：将所有docs作为同一个PDF的不同页面
    pdf_names = ["Scientific_Knowledge_Base.pdf"] * len(docs)  # 统一PDF名称
    page_numbers = list(range(1, len(docs) + 1))  # 页码从1开始
    is_blocked_list = [False] * len(docs)  # 全部未被屏蔽
    collection_name = "rag_docs"
    
    # 使用新的元数据插入方法
    print("插入科学知识库数据...")
    insert.insert_data_with_metadata(
        texts=docs,
        pdf_names=pdf_names,
        page_numbers=page_numbers,
        is_blocked_list=is_blocked_list,
        collection_name=collection_name
    )
    
    # 使用新的过滤搜索方法
    queries = ["What's DNA?", "What is the speed of light?"]
    results = []
    for query in queries:
        results.append(refer.get_reference_with_filter(
            query=query,
            collection_name=collection_name,
            only_unblocked=True  # 只搜索未被屏蔽的文档
        ))
    
    print("Search Results:")
    for i, result_group in enumerate(results):
        print(f"Query {i+1} ({queries[i]}) results:")
        for result in result_group:
            print(f"  - 序号: {result['index']}, 相关度: {result['relevance_score']:.3f}")
            print(f"    PDF: {result['pdf_name']}, 页码: {result['page_number']}")
            print(f"    文本: {result['text'][:100]}...")
            print()


def demo_metadata_filtering():
    """演示元数据过滤功能"""
    print("\n=== 元数据过滤功能演示 ===")
    
    # 准备带有元数据的示例数据
    texts = [
        "人工智能是计算机科学的一个分支，它企图了解智能的实质。",
        "机器学习是人工智能的一个分支，专门研究计算机怎样模拟人类的学习行为。",
        "深度学习是机器学习研究中的一个新的领域，动机在于建立、模拟人脑的神经网络。",
        "自然语言处理是人工智能的一个重要分支，研究人与计算机之间的自然语言通信。",
        "计算机视觉是一门研究如何使机器'看'的科学，用摄影机和电脑代替人眼。"
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
    
    collection_name = "rag_docs_demo"
    
    try:
        print("插入带元数据的数据...")
        insert.insert_data_with_metadata(
            texts=texts,
            pdf_names=pdf_names,
            page_numbers=page_numbers,
            is_blocked_list=is_blocked_list,
            collection_name=collection_name
        )
        
        print("测试元数据过滤搜索...")
        query = "什么是人工智能"
        
        # 测试普通搜索 vs 过滤搜索
        print("\n普通搜索（可能包含被屏蔽的文档）:")
        normal_results = refer.get_reference_with_filter(
            query=query,
            collection_name=collection_name,
            only_unblocked=False
        )
        for result in normal_results[:3]:
            print(f"  - {result['pdf_name']}: {result['text'][:50]}...")
        
        print("\n过滤搜索（排除被屏蔽的文档）:")
        filtered_results = refer.get_reference_with_filter(
            query=query,
            collection_name=collection_name,
            only_unblocked=True
        )
        for result in filtered_results[:3]:
            print(f"  - {result['pdf_name']}: {result['text'][:50]}...")
        
        print("\n排除特定PDF:")
        excluded_results = refer.get_reference_with_filter(
            query=query,
            collection_name=collection_name,
            excluded_pdfs=["AI基础教程.pdf"],
            only_unblocked=True
        )
        for result in excluded_results[:3]:
            print(f"  - {result['pdf_name']}: {result['text'][:50]}...")
        
        # 显示PDF管理信息
        print("\nPDF管理信息:")
        manager = PDFManager(collection_name)
        stats = manager.get_pdf_stats()
        print(f"  总PDF数: {stats.get('total_pdfs', 0)}")
        print(f"  被屏蔽PDF数: {stats.get('blocked_pdfs', 0)}")
        print(f"  正常PDF数: {stats.get('unblocked_pdfs', 0)}")
        
    except Exception as e:
        print(f"元数据过滤演示失败: {e}")


def main():
    print("Hello from RAG!")
    
    # 演示基础功能（现在使用新的元数据过滤模块）
    demo_basic_functionality()
    
    # 演示元数据过滤功能
    demo_metadata_filtering()
    
    print("\n=== 演示完成 ===")
    print("\n提示:")
    print("1. 基础功能现在也使用新的元数据过滤模块")
    print("2. docs被作为 'Scientific_Knowledge_Base.pdf' 处理，状态为未屏蔽")
    print("3. 运行 metadata_filter_example.py 查看完整的元数据过滤示例")
    print("4. 使用 rag_modules.pdf_manager.PDFManager 管理PDF文档状态")
    print("5. 使用 rag_modules.refer.get_reference_with_filter 进行过滤搜索")


if __name__ == "__main__":
    main()
