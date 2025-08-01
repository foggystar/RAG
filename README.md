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
.
├── ans.md
├── api_client.py
├── config.py
├── docs
│   ├── CONCURRENT_EMBEDDING_GUIDE.md
│   ├── filter.md
│   ├── METADATA_FILTERING_GUIDE.md
│   ├── RAG技术栈概览.md
│   └── STM32F103x8.pdf
├── fastapi_test.py
├── main.py
├── milvus_rag.db
├── __pycache__
│   ├── api_client.cpython-312.pyc
│   ├── config.cpython-312.pyc
│   └── fastapi_test.cpython-312.pyc
├── pyproject.toml
├── rag_modules
│   ├── clear.py
│   ├── embedding.py
│   ├── __init__.py
│   ├── insert.py
│   ├── pdf_manager.py
│   ├── __pycache__
│   │   ├── clear.cpython-312.pyc
│   │   ├── clear.cpython-313.pyc
│   │   ├── embedding.cpython-312.pyc
│   │   ├── __init__.cpython-312.pyc
│   │   ├── __init__.cpython-313.pyc
│   │   ├── insert.cpython-312.pyc
│   │   ├── pdf_manager.cpython-312.pyc
│   │   ├── refer.cpython-312.pyc
│   │   ├── reranker.cpython-312.pyc
│   │   └── search.cpython-312.pyc
│   ├── refer.py
│   ├── reranker.py
│   └── search.py
├── README.md
├── sys_board.md
├── utilties
│   ├── colored_logger.py
│   ├── __init__.py
│   ├── load_pdf.py
│   ├── __pycache__
│   │   ├── colored_logger.cpython-312.pyc
│   │   ├── colored_logger.cpython-313.pyc
│   │   ├── __init__.cpython-312.pyc
│   │   ├── __init__.cpython-313.pyc
│   │   ├── load_pdf.cpython-312.pyc
│   │   └── query.cpython-312.pyc
│   └── query.py
└── uv.lock

```
