# RAG 检索增强生成系统

一个基于 Milvus 向量数据库的检索增强生成(RAG)系统，支持PDF文档管理、元数据过滤、重排序等高级功能。

## 🚀 特性

- **向量化文本存储**: 使用 Milvus 向量数据库存储文本 embeddings
- **元数据过滤**: 支持基于PDF文件名、页码、屏蔽状态的过滤搜索
- **智能重排序**: 集成重排序算法提升搜索准确性
- **PDF文档管理**: 支持文档屏蔽/解除屏蔽功能
- **批量并发处理**: 支持大规模文本的高效向量化
- **灵活的搜索选项**: 多种搜索策略)

# 4. 处理结果
for ref in references:
    print(f"来源: {ref['pdf_name']}")
    print(f"相关度: {ref['relevance_score']:.3f}")
    print(f"内容: {ref['text']}")
    print("-" * 50)
```

## 🔧 配置选项

- **数据库文件**: 默认为 `milvus_rag.db`
- **集合名称**: 默认为 `rag_docs`
- **向量维度**: 768维 (使用Qwen3-Embedding-4B模型)
- **重排序阈值**: 相关度分数 >= 0.2

## 🔗 相关资源

- [Milvus 官方文档](https://milvus.io/docs)
- [SiliconFlow API 文档](https://docs.siliconflow.cn/)
## 📁 项目结构

```
RAG/
├── main.py                           # 主程序入口和基础功能演示
├── metadata_filter_example.py       # 元数据过滤功能示例
├── pyproject.toml                   # 项目配置和依赖管理
├── milvus_rag.db                    # Milvus 数据库文件
├── README.md                        # 项目说明文档
├── uv.lock                          # 依赖锁定文件
├── docs/                            # 文档目录
│   ├── CONCURRENT_EMBEDDING_GUIDE.md     # 并发嵌入指南
│   ├── filter.md                         # 过滤功能说明
│   ├── METADATA_FILTERING_GUIDE.md       # 元数据过滤指南
│   └── RAG技术栈概览.md                   # RAG技术栈概览
└── rag_modules/                     # 核心模块目录
    ├── __init__.py                  # 模块初始化
    ├── clear.py                     # 数据清理模块
    ├── embedding.py                 # 文本向量化模块
    ├── insert.py                    # 数据插入模块
    ├── pdf_manager.py               # PDF文档管理模块
    ├── refer.py                     # 参考文档获取模块
    ├── reranker.py                  # 重排序模块
    └── search.py                    # 搜索模块
```

## 🛠️ 安装配置

### 环境要求

- Python >= 3.12
- UV 包管理器 (推荐) 或 pip

### 依赖安装

使用 UV (推荐):
```bash
# 克隆项目
git clone <repository-url>
cd RAG

# 安装依赖
uv sync
```

使用 pip:
```bash
pip install fastapi langchain-google-genai langchain-milvus openai pymilvus pypdf
```

### 环境变量配置

设置API密钥：
```bash
export siliconflow_api_key="your_api_key_here"
```

## 📚 核心模块使用指南

### 1. embedding.py - 文本向量化模块

负责将文本转换为向量表示，支持单个文本和批量处理。

**主要功能**:
- `get_embedding()`: 获取单个文本的向量
- `get_batch_embeddings_large_scale()`: 批量处理大规模文本向量化

**使用示例**:
```python
from rag_modules.embedding import get_embedding, get_batch_embeddings_large_scale

# 单个文本向量化
vector = get_embedding("人工智能是计算机科学的一个分支")

# 批量文本向量化
texts = ["文本1", "文本2", "文本3"]
vectors = get_batch_embeddings_large_scale(texts)
```

### 2. insert.py - 数据插入模块

用于创建集合和插入带有元数据的文档数据。

**主要功能**:
- `create_rag_collection()`: 创建带有元数据字段的RAG集合
- `insert_data_with_metadata()`: 插入带有完整元数据的文档

**集合Schema**:
- `id`: 主键 (INT64)
- `vector`: 向量字段 (FLOAT_VECTOR, 768维)
- `text_content`: 文本内容 (VARCHAR)
- `pdf_name`: PDF文件名 (VARCHAR)
- `page_number`: 页码 (INT64)
- `is_blocked`: 屏蔽状态 (BOOL)

**使用示例**:
```python
from rag_modules.insert import insert_data_with_metadata

texts = ["文档内容1", "文档内容2"]
pdf_names = ["document1.pdf", "document2.pdf"]
page_numbers = [1, 1]
is_blocked_list = [False, True]  # document2.pdf被屏蔽

insert_data_with_metadata(
    texts=texts,
    pdf_names=pdf_names,
    page_numbers=page_numbers,
    is_blocked_list=is_blocked_list,
    collection_name="my_docs"
)
```

### 3. search.py - 搜索模块

提供多种搜索策略和过滤功能。

**主要功能**:
- `search_with_metadata_filter()`: 带元数据过滤的搜索
- `search_only_unblocked()`: 只搜索未屏蔽文档
- 支持复杂的过滤表达式

**使用示例**:
```python
from rag_modules.search import search_with_metadata_filter, search_only_unblocked

# 基础搜索
results = search_with_metadata_filter(
    query=["什么是人工智能"],
    collection_name="rag_docs",
    limit=5
)

# 过滤搜索：排除特定PDF
results = search_with_metadata_filter(
    query=["机器学习"],
    collection_name="rag_docs",
    expr="pdf_name != 'secret_doc.pdf'",
    limit=5
)

# 只搜索未屏蔽文档
results = search_only_unblocked(
    query=["深度学习"],
    collection_name="rag_docs",
    limit=5
)
```

### 4. refer.py - 参考文档模块

集成搜索和重排序，提供高质量的参考文档。

**主要功能**:
- `get_reference_with_filter()`: 获取带过滤的重排序参考文档

**使用示例**:
```python
from rag_modules.refer import get_reference_with_filter

# 获取参考文档，排除特定PDF且只包含未屏蔽文档
references = get_reference_with_filter(
    query="自然语言处理",
    collection_name="rag_docs",
    excluded_pdfs=["old_version.pdf"],
    only_unblocked=True,
    limit=5
)

for ref in references:
    print(f"相关度: {ref['relevance_score']:.3f}")
    print(f"来源: {ref['pdf_name']} 第{ref['page_number']}页")
    print(f"内容: {ref['text'][:100]}...")
```

### 5. reranker.py - 重排序模块

使用重排序算法优化搜索结果的相关性排序。

**主要功能**:
- `get_rerank()`: 对搜索结果进行重排序

### 6. pdf_manager.py - PDF文档管理模块

提供PDF文档的屏蔽和管理功能。

**主要功能**:
- `PDFManager`: PDF文档管理器类
- `block_pdf()`: 屏蔽PDF文档
- `unblock_pdf()`: 解除屏蔽PDF文档
- `list_all_pdfs()`: 列出所有PDF文档
- `get_blocked_pdfs()`: 获取被屏蔽的PDF列表

**使用示例**:
```python
from rag_modules.pdf_manager import PDFManager

manager = PDFManager(collection_name="rag_docs")

# 列出所有PDF
all_pdfs = manager.list_all_pdfs()

# 屏蔽特定PDF
manager.block_pdf("sensitive_document.pdf")

# 获取被屏蔽的PDF列表
blocked_pdfs = manager.get_blocked_pdfs()
```

### 7. clear.py - 数据清理模块

提供数据库清理功能。

**使用示例**:
```python
from rag_modules.clear import clear_data

# 清除所有数据
clear_data()

# 清除特定集合
clear_data(collection_name="specific_collection")
```

## 🎯 完整使用示例

### 基础RAG流程

```python
from rag_modules.insert import insert_data_with_metadata
from rag_modules.refer import get_reference_with_filter
from rag_modules.clear import clear_data

# 1. 清理旧数据
clear_data()

# 2. 准备文档数据
texts = [
    "人工智能是计算机科学的一个分支",
    "机器学习是人工智能的重要组成部分",
    "深度学习使用神经网络进行学习"
]
pdf_names = ["AI教程.pdf", "ML指南.pdf", "DL详解.pdf"]
page_numbers = [1, 1, 1]
is_blocked_list = [False, False, True]  # 屏蔽深度学习文档

# 3. 插入数据
insert_data_with_metadata(
    texts=texts,
    pdf_names=pdf_names,
    page_numbers=page_numbers,
    is_blocked_list=is_blocked_list
)

# 4. 搜索并获取参考文档
references = get_reference_with_filter(
    query="什么是人工智能",
    only_unblocked=True,  # 只搜索未屏蔽文档
    limit=3
)

# 5. 处理结果
for ref in references:
    print(f"来源: {ref['pdf_name']}")
    print(f"相关度: {ref['relevance_score']:.3f}")
    print(f"内容: {ref['text']}")
    print("-" * 50)
```

## 🔧 配置选项

- **数据库文件**: 默认为 `milvus_rag.db`
- **集合名称**: 默认为 `rag_docs`
- **向量维度**: 768维 (使用Qwen3-Embedding-4B模型)
- **重排序阈值**: 相关度分数 >= 0.2

## 🔗 相关资源

- [Milvus 官方文档](https://milvus.io/docs)
- [SiliconFlow API 文档](https://docs.siliconflow.cn/)