# 元数据过滤功能使用指南

本指南说明如何使用新的Milvus Collection schema进行PDF文档的元数据过滤，包括屏蔽特定PDF文档和按条件搜索。

## 功能概述

根据 `filter.md` 中的推荐方案，我们实现了**单个Collection + Metadata Filtering (元数据过滤)**的解决方案。

### 核心特性

1. **统一存储**: 所有PDF文档的数据存储在同一个Milvus Collection中
2. **元数据字段**: 包含PDF文件名、页码、屏蔽状态等元数据
3. **灵活过滤**: 支持多种过滤条件的组合
4. **动态管理**: 可以动态屏蔽/解除屏蔽PDF文档

## 新的Schema结构

```python
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768),  # 向量维度
    FieldSchema(name="text_content", dtype=DataType.VARCHAR, max_length=65535),  # 原始文本
    FieldSchema(name="pdf_name", dtype=DataType.VARCHAR, max_length=256),  # PDF文件名
    FieldSchema(name="page_number", dtype=DataType.INT64),  # 页码
    FieldSchema(name="is_blocked", dtype=DataType.BOOL)  # 是否被屏蔽
]
```

## 主要功能模块

### 1. 数据插入 (`rag_modules/insert.py`)

- `create_rag_collection()`: 创建带有元数据字段的Collection
- `insert_data_with_metadata()`: 插入带有元数据的数据

```python
from rag_modules.insert import insert_data_with_metadata

# 插入带元数据的数据
insert_data_with_metadata(
    texts=["文本内容1", "文本内容2"],
    pdf_names=["文档1.pdf", "文档2.pdf"],
    page_numbers=[1, 2],
    is_blocked_list=[False, True],  # 文档2被屏蔽
    collection_name="rag_docs"
)
```

### 2. 搜索和过滤 (`rag_modules/search.py`)

- `search_with_metadata_filter()`: 基础元数据过滤搜索
- `search_exclude_pdfs()`: 排除特定PDF文档
- `search_only_unblocked()`: 只搜索未被屏蔽的文档

```python
from rag_modules.search import search_only_unblocked, search_exclude_pdfs

# 只搜索未被屏蔽的文档
results = search_only_unblocked(["查询内容"], "rag_docs", limit=10)

# 排除特定PDF
results = search_exclude_pdfs(["查询内容"], ["不想要的.pdf"], "rag_docs", limit=10)
```

### 3. 智能检索 (`rag_modules/refer.py`)

- `get_reference_with_filter()`: 带有元数据过滤的智能检索（包含重排序）

```python
from rag_modules.refer import get_reference_with_filter

# 复合过滤：排除被屏蔽的文档和特定PDF
results = get_reference_with_filter(
    query="什么是人工智能",
    collection_name="rag_docs",
    excluded_pdfs=["过时文档.pdf"],
    only_unblocked=True
)
```

### 4. PDF管理 (`rag_modules/pdf_manager.py`)

- `PDFManager`: PDF文档管理器，用于查看和管理PDF状态

```python
from rag_modules.pdf_manager import PDFManager

manager = PDFManager("rag_docs")

# 列出所有PDF
all_pdfs = manager.list_pdfs()

# 只列出被屏蔽的PDF
blocked_pdfs = manager.list_pdfs(only_blocked=True)

# 获取统计信息
stats = manager.get_pdf_stats()
```

## 使用示例

### 基础使用

```python
# 运行主程序查看演示
python main.py

# 运行完整的元数据过滤示例
python metadata_filter_example.py
```

### 过滤表达式示例

```python
# 只搜索未被屏蔽的文档
expr = "is_blocked == false"

# 排除特定PDF
expr = "pdf_name != '秘密文档.pdf'"

# 排除多个PDF
expr = "pdf_name not in ('文档1.pdf', '文档2.pdf')"

# 复合条件
expr = "is_blocked == false AND pdf_name != '过时文档.pdf'"
```

## 优势

1. **灵活性**: 可以根据任何元数据字段进行筛选
2. **集中管理**: 所有数据在一个Collection中，便于管理
3. **高效查询**: Milvus的标量字段过滤性能优异
4. **动态调整**: 无需重建索引即可调整文档可见性
5. **跨PDF搜索**: 默认跨所有PDF搜索，通过过滤器排除不需要的内容

## 注意事项

1. **Milvus版本**: 确保使用支持标量字段过滤的Milvus版本
2. **索引优化**: 为常用的过滤字段建立适当的索引
3. **表达式语法**: 遵循Milvus的布尔表达式语法规范
4. **数据一致性**: 插入数据时确保元数据字段的完整性

## 扩展功能

- 可以添加更多元数据字段（如文档类型、创建时间等）
- 支持更复杂的过滤逻辑
- 与权限系统集成实现用户级别的文档访问控制
