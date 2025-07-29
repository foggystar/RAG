

#### 3. **推荐方案：单个Collection + Metadata Filtering (元数据过滤)**

*   **这是最灵活和推荐的方案。**
*   **核心思想:**
    *   所有来自不同PDF的资料都存储在**同一个Milvus Collection**中。
    *   在Collection的Schema中，添加一个或多个**标量字段 (Scalar Fields)** 来存储PDF的元数据。
        *   例如：`pdf_id` (唯一标识PDF), `pdf_name` (PDF文件名), `is_blocked` (布尔值，表示是否被屏蔽), `status` (例如：`'active'`, `'blocked'`, `'pending'`) 等。
    *   当进行向量搜索时，通过**布尔表达式 (Boolean Expression)** 对这些元数据字段进行过滤。

*   **优点:**
    *   **极度灵活:** 可以根据任何元数据字段进行筛选。要屏蔽某个PDF，只需更新其`is_blocked`字段为`true`，或在查询时添加`pdf_id != '要屏蔽的PDF的ID'`。
    *   **集中管理:** 所有数据都在一个Collection中，管理维护更方便。
    *   **高效查询:** Milvus的标量字段过滤通常非常高效，尤其是在字段上建立索引（例如Inverted Index或Bloom Filter）。你可以在一次查询中轻松地排除不需要的数据。
    *   **动态调整:** 可以在不改变数据结构的情况下，动态地开启或关闭某个PDF的可见性。
    *   **跨PDF搜索自然:** 默认情况下，搜索会跨所有PDF（因为都在一个Collection），然后通过过滤器排除不需要的。

*   **如何实现:**
    1.  **创建Collection时定义Schema:**
        ```python
        from pymilvus import FieldSchema, CollectionSchema, DataType, Collection

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768), # 你的向量维度
            FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=65535), # 存储原始文本片段
            FieldSchema(name="pdf_name", dtype=DataType.VARCHAR, max_length=256), # PDF文件名
            FieldSchema(name="page_number", dtype=DataType.INT64), # 页码
            FieldSchema(name="is_blocked", dtype=DataType.BOOL) # 是否被屏蔽的标志
        ]
        schema = CollectionSchema(fields, "Collection for RAG documents")
        collection = Collection("rag_docs", schema)
        ```
    2.  **插入数据时包含元数据:**
        ```python
        # 假设你有一个PDF的ID和其内容
        pdf_id = "doc_abc_123"
        pdf_name = "秘密项目报告.pdf"
        page_num = 1
        text_chunk = "这是秘密项目的关键信息。"
        embedding = [0.1, 0.2, ...] # 你的向量
        
        entities = [
            {"id": 1, "vector": embedding, "text_content": text_chunk, "pdf_name": pdf_name, "page_number": page_num, "is_blocked": False}
        ]
        collection.insert(entities)
        ```
    3.  **查询时进行过滤:**
        *   **只搜索未被屏蔽的PDF：**
            ```python
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = collection.search(
                data=[query_vector], 
                anns_field="vector", 
                param=search_params,
                limit=10, 
                expr="is_blocked == false", # 核心过滤条件
                output_fields=["text_content", "pdf_name", "page_number"]
            )
            ```
        *   **排除某个特定的PDF：**
            ```python
            results = collection.search(
                data=[query_vector], 
                anns_field="vector", 
                param=search_params,
                limit=10, 
                expr="pdf_name != '秘密项目报告.pdf'", # 或 "pdf_id != 'doc_abc_123'"
                output_fields=["text_content", "pdf_name", "page_number"]
            )
            ```
        *   **排除多个特定的PDF：**
            ```python
            # 注意：对于字符串列表，通常使用 IN/NOT IN 操作符
            excluded_pdfs = ["秘密项目报告.pdf", "过时文件.pdf"]
            excluded_expr = f"pdf_name not in {excluded_pdfs}" # 字符串格式化可能会因库而异，确保Milvus能解析
            
            # 或者更通用的构建方式
            excluded_conditions = [f"pdf_name != '{p}'" for p in excluded_pdfs]
            final_expr = " AND ".join(excluded_conditions)
            
            # 也可以直接在Python中构建IN/NOT IN的表达式
            expr = f"pdf_name not in {str(excluded_pdfs).replace('[', '(').replace(']', ')')}" # ('pdf1.pdf', 'pdf2.pdf')
            
            results = collection.search(
                data=[query_vector], 
                anns_field="vector", 
                param=search_params,
                limit=10, 
                expr=expr, # 使用构建好的表达式
                output_fields=["text_content", "pdf_name", "page_number"]
            )
            ```
