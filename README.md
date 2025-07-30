# RAG 检索增强生成系统

一个基于 Milvus 向量数据库的智能文档检索增强生成(RAG)系统，专为PDF文档处理和智能问答而设计。支持文档解析、向量化存储、语义搜索、多轮问答等完整的RAG流程。

## ✨ 核心特性

- **智能PDF解析**: 基于LangChain的PDF语义分割，保持文档结构和语义完整性
- **高效向量存储**: 使用Milvus Lite数据库进行向量化文本存储和快速检索
- **智能文本分割**: 支持复杂问题的自动分解和多角度查询
- **重排序优化**: 集成重排序算法提升检索结果的相关性和准确性
- **多模型支持**: 集成SiliconFlow API，支持多种大语言模型和嵌入模型
- **命令行界面**: 提供便捷的CLI工具，支持文档加载、查询、清理等操作
- **并发处理**: 支持大规模文档的高效批量处理

## 🏗️ 系统架构

```
RAG 系统流程:
PDF文档 → 智能解析 → 文本分割 → 向量化 → Milvus存储
                ↓
用户问题 → 问题分解 → 向量检索 → 重排序 → 大模型生成 → 答案输出
```
## 🚀 快速开始

### 环境要求

- Python >= 3.12
- UV 包管理器 (推荐) 或 pip

### 安装依赖

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
pip install bs4 langchain-community openai pdfminer-six pymilvus requests
```

### 环境变量配置

设置SiliconFlow API密钥：
```bash
export siliconflow_api_key="your_api_key_here"
```

### 基本使用

1. **加载PDF文档**：
```bash
python main.py --load docs/example.pdf
```

2. **查询文档内容**：
```bash
python main.py --query "什么是STM32微控制器的引脚配置？"
```

3. **复杂查询（自动问题分解）**：
```bash
python main.py --query "STM32F103的封装类型和引脚配置" --split
```

4. **指定文档查询**：
```bash
python main.py --query "GPIO配置方法" --include docs/STM32F103x8.pdf
```

5. **清理数据库**：
```bash
python main.py --clear
```

## 📁 项目结构

```
RAG/
├── main.py                    # 主程序入口和命令行工具
├── pyproject.toml            # 项目配置和依赖管理
├── uv.lock                   # 依赖锁定文件
├── milvus_rag.db            # Milvus 数据库文件
├── README.md                # 项目说明文档
├── ans.md                   # 查询结果示例
├── test.html                # PDF解析测试文件
├── docs/                    # 文档目录
│   ├── STM32F103x8.pdf      # 示例PDF文档
│   └── *.md                 # 技术文档和指南
├── rag_modules/             # 核心RAG模块
│   ├── __init__.py          # 模块初始化
│   ├── clear.py             # 数据清理模块
│   ├── embedding.py         # 文本向量化模块
│   ├── insert.py            # 数据插入模块
│   ├── pdf_manager.py       # PDF文档管理模块
│   ├── refer.py             # 参考文档获取模块
│   ├── reranker.py          # 重排序模块
│   └── search.py            # 搜索模块
└── utilties/                # 工具模块
    ├── __init__.py          # 模块初始化
    ├── load_pdf.py          # PDF加载和解析
    └── query.py             # 查询处理和答案生成
```

## � 核心模块详解

### 1. `utilties/load_pdf.py` - PDF智能解析模块

专门处理PDF文档的解析和语义分割，基于LangChain的PDFMinerPDFasHTMLLoader：

**主要功能**:
- 将PDF转换为HTML格式进行解析
- 基于字体大小识别标题和内容层次
- 自动检测页面分隔符并维护页码信息
- 生成语义分割的文档片段

**使用示例**:
```python
from utilties.load_pdf import load_pdf

# 解析PDF文档
semantic_snippets = load_pdf("docs/STM32F103x8.pdf")

# 查看解析结果
for snippet in semantic_snippets:
    print(f"标题: {snippet.metadata['heading']}")
    print(f"页码: {snippet.metadata['page_number']}")
    print(f"内容: {snippet.page_content[:100]}...")
```

### 2. `utilties/query.py` - 查询处理模块

负责处理用户查询、问题分解和答案生成：

**主要功能**:
- `split_query()`: 智能分解复杂问题为多个子问题
- `query_to_database()`: 从数据库检索相关文档
- `ans()`: 基于检索结果生成最终答案

**使用示例**:
```python
from utilties.query import split_query, query_to_database, ans

# 分解复杂问题
questions = split_query("STM32F103的引脚配置和GPIO设置方法")

# 检索相关文档
results = query_to_database("GPIO配置", ["STM32F103x8.pdf"])

# 生成答案
answer = ans(questions, results)
```

### 3. `rag_modules/embedding.py` - 文本向量化模块

高效的文本向量化处理，支持单个和批量处理：

**主要功能**:
- `get_embedding()`: 单个文本向量化
- `get_batch_embeddings()`: 批量文本向量化
- `get_batch_embeddings_large_scale()`: 大规模并发向量化

**技术特性**:
- 使用Qwen3-Embedding-4B模型，768维向量
- 支持多线程并发处理
- 自动错误处理和重试机制

### 4. `rag_modules/insert.py` - 数据插入模块

负责将处理后的文档数据插入Milvus数据库：

**数据结构**:
- `id`: 唯一标识符 (INT64)
- `vector`: 768维向量 (FLOAT_VECTOR)
- `text_content`: 文本内容 (VARCHAR)
- `pdf_name`: PDF文件名 (VARCHAR)
- `page_number`: 页码 (INT64)
- `is_blocked`: 屏蔽状态 (BOOL) # 弃用,暂未删除

### 5. `rag_modules/search.py` - 智能搜索模块

提供多种搜索策略和过滤功能：

**主要功能**:
- 向量相似度搜索
- 元数据过滤
- 多条件组合查询
- 结果排序和优化

### 6. `rag_modules/refer.py` - 参考文档获取模块

集成搜索和重排序，提供高质量的参考文档：

**工作流程**:
1. 向量检索获取候选文档
2. 重排序算法优化结果排序
3. 过滤和筛选最相关的文档
4. 返回结构化的参考信息

## 💡 使用场景示例

### 场景1: 技术文档问答

```bash
# 加载技术文档
python main.py --load docs/STM32F103x8.pdf

# 查询具体技术问题
python main.py --query "STM32F103的GPIO引脚如何配置为输出模式？"

# 复杂技术问题分解查询
python main.py --query "STM32F103的封装类型、引脚配置和GPIO设置方法" --split
```

### 场景2: 多文档对比分析

```bash
# 加载多个相关文档
python main.py --load docs/doc1.pdf --load docs/doc2.pdf

# 指定文档范围查询
python main.py --query "比较不同型号的特性" --include docs/doc1.pdf --include docs/doc2.pdf
```

### 场景3: 批量文档处理

```bash
# 批量加载文档目录
for file in docs/*.pdf; do
    python main.py --load "$file"
done

# 跨文档查询
python main.py --query "微控制器的通用特性"
```

## 🎯 完整使用示例

### 基础RAG工作流程

```python
# 完整的RAG流程示例
from utilties.load_pdf import load_pdf
from rag_modules.insert import insert_data_with_metadata
from utilties.query import query_to_database, ans
from rag_modules.clear import clear_data

# 1. 清理旧数据
clear_data()

# 2. 加载和解析PDF文档
semantic_snippets = load_pdf("docs/STM32F103x8.pdf")

# 3. 准备插入数据
texts = []
pdf_names = []
page_numbers = []

for snippet in semantic_snippets:
    texts.append(snippet.page_content)
    pdf_names.append("STM32F103x8.pdf")
    page_numbers.append(snippet.metadata['page_number'])

# 4. 插入数据到向量数据库
insert_data_with_metadata(
    texts=texts,
    pdf_names=pdf_names,
    page_numbers=page_numbers
)

# 5. 查询文档
question = "STM32F103的GPIO引脚如何配置？"
references = query_to_database(question, ["STM32F103x8.pdf"])

# 6. 生成答案
final_answer = ans([question], references)
print(final_answer)
```

### 命令行工具使用

系统提供了强大的命令行界面，支持以下操作：

```bash
# 基础用法
python main.py <command> [args]

# 可用命令:
--load <pdf_name>     # 加载PDF文档
--clear               # 清理数据库
--query <question>    # 查询问题
--include <pdf_name>  # 指定查询范围
--split               # 启用问题分解
```

**实际使用示例**:

```bash
# 1. 加载文档
python main.py --load docs/STM32F103x8.pdf

# 2. 简单查询
python main.py --query "什么是STM32F103？"

# 3. 复杂查询（自动分解问题）
python main.py --query "STM32F103的引脚配置和GPIO设置" --split

# 4. 多文档加载
python main.py --load docs/doc1.pdf --load docs/doc2.pdf

# 5. 指定文档查询
python main.py --query "GPIO配置方法" --include docs/STM32F103x8.pdf

# 6. 组合命令
python main.py --clear --load docs/new_doc.pdf --query "新文档内容摘要"
```

## ⚙️ 配置说明

### 模型配置

- **嵌入模型**: Qwen/Qwen3-Embedding-4B (768维)
- **生成模型**: moonshotai/Kimi-K2-Instruct (可配置)
- **问题分解模型**: Qwen/Qwen3-30B-A3B (可配置)

### 数据库配置

- **数据库类型**: Milvus Lite
- **数据库文件**: `milvus_rag.db`
- **默认集合**: `rag_docs`
- **向量维度**: 768

### API配置

需要配置SiliconFlow API密钥：
```bash
export siliconflow_api_key="your_api_key_here"
```

## 🔍 技术原理

### 文档处理流程

1. **PDF解析**: 使用PDFMiner提取PDF的HTML表示
2. **语义分割**: 基于字体大小和布局识别文档结构
3. **内容提取**: 保留标题层次和页码信息
4. **向量化**: 使用高质量嵌入模型转换为向量表示

### 检索策略

1. **向量检索**: 基于语义相似度的快速检索
2. **重排序**: 使用重排序模型优化结果排序
3. **过滤机制**: 支持基于元数据的精确过滤
4. **结果聚合**: 智能合并和去重相似结果

### 答案生成

1. **问题理解**: 自动分析和分解复杂问题
2. **上下文构建**: 基于检索结果构建相关上下文
3. **答案合成**: 使用大语言模型生成准确答案
4. **引用标注**: 自动添加源文档引用信息

## 📊 性能优化

- **并发处理**: 支持多线程向量化，提升处理速度
- **批量操作**: 优化大规模文档的处理效率
- **缓存机制**: 智能缓存常用查询结果
- **内存管理**: 自动清理临时数据，避免内存泄漏

## 🔗 相关资源

- [Milvus 官方文档](https://milvus.io/docs)
- [SiliconFlow API 文档](https://docs.siliconflow.cn/)
- [LangChain 文档](https://python.langchain.com/)

## 📝 注意事项

1. **API配额**: 注意SiliconFlow API的使用配额限制
2. **文档格式**: 建议使用结构清晰的PDF文档以获得最佳效果
3. **内存使用**: 大文档处理时注意内存使用情况
4. **网络连接**: 确保网络连接稳定以访问在线API服务

