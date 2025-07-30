from rag_modules import insert, clear, refer
from rag_modules.pdf_manager import PDFManager


def main():
    """RAG系统基础演示"""
    print("=== RAG 检索增强生成系统演示 ===\n")
    
    collection_name = "rag_docs"
    
    # 科学知识库示例数据
    docs = [
        "牛顿运动定律是经典力学的基础。",
        "元素周期表按原子序数和性质组织元素。",
        "DNA携带所有生物体的遗传信息。",
        "光合作用将阳光转化为植物的化学能。",
        "爱因斯坦的相对论彻底改变了我们对时空的理解。",
        "线粒体被称为细胞的动力工厂。",
        "量子力学描述原子尺度物质的行为。",
        "真空中的光速约为299,792,458米/秒。",
        "化学键在原子共享或转移电子时形成。",
        "人脑约含有860亿个神经元。"
    ]
    
    try:
        # 1. 清理旧数据
        print("1. 清理旧数据...")
        clear.clear_data(collection_name=collection_name)
        
        # 2. 插入科学知识库数据
        print("2. 插入科学知识库数据...")
        pdf_names = ["科学知识库.pdf"] * len(docs)
        page_numbers = list(range(1, len(docs) + 1))
        is_blocked_list = [False] * len(docs)  # 全部未屏蔽
        
        insert.insert_data_with_metadata(
            texts=docs,
            pdf_names=pdf_names,
            page_numbers=page_numbers,
            is_blocked_list=is_blocked_list,
            collection_name=collection_name
        )
        
        # 3. 搜索测试
        print("\n3. 搜索测试...")
        queries = ["什么是DNA?", "光速是多少?", "牛顿定律"]
        
        for query in queries:
            print(f"\n查询: {query}")
            results = refer.get_reference_with_filter(
                query=query,
                collection_name=collection_name,
                only_unblocked=True,
                limit=3
            )
            
            for result in results[:2]:  # 只显示前2个结果
                print(f"  - 相关度: {result['relevance_score']:.3f}")
                print(f"    页码: {result['page_number']}, 内容: {result['text'][:50]}...")
        
        # 4. PDF管理演示
        print("\n4. PDF管理信息:")
        manager = PDFManager(collection_name)
        stats = manager.get_pdf_stats()
        print(f"  总PDF数: {stats.get('total_pdfs', 0)}")
        print(f"  文档块数: {stats.get('total_chunks', 0)}")
        
        print("\n✓ 演示完成！")
        
    except Exception as e:
        print(f"✗ 演示失败: {e}")


if __name__ == "__main__":
    main()
