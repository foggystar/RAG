# RAG 检索增强生成系统

## 项目简介

这是一个基于 Milvus 向量数据库的检索增强生成（RAG）系统，专为处理 PDF 文档而设计。该系统结合了现代 AI 技术，提供智能文档查询和问答功能，支持中文处理，并提供友好的 Web 界面。

## 核心功能

### 📁 文档管理
- **PDF 导入**: 上传并自动处理 PDF 文件，提取文本内容并创建向量索引
- **文档列表**: 查看所有已导入的 PDF 文件
- **活跃文档设置**: 选择当前查询中要使用的 PDF 文档
- **数据清理**: 一键清除数据库中的所有文档数据

### 🔍 智能查询
- **语义搜索**: 基于向量相似度的智能文档检索
- **重排序优化**: 使用 AI 模型对检索结果进行重排序，提高相关性
- **流式响应**: 支持实时流式输出，提升用户体验
- **多 PDF 联合查询**: 可同时从多个选定的 PDF 文档中检索信息

### 🧠 AI 增强
- **多模型支持**: 集成多种 AI 模型用于不同任务
  - 嵌入模型：Qwen/Qwen3-Embedding-4B
  - 查询分割：Qwen/Qwen3-30B-A3B-Instruct-2507
  - 对话生成：deepseek-ai/DeepSeek-V3
  - 重排序：Qwen/Qwen3-Reranker-4B
- **查询优化**: 自动分析和优化用户查询
- **上下文感知**: 基于文档内容生成准确的答案

### 🌐 Web 界面
- **响应式设计**: 现代化的 Web 界面，支持桌面和移动设备
- **实时交互**: 支持文件拖拽上传、实时查询反馈
- **答案保存**: 自动保存查询结果到本地文件
- **图像支持**: 智能处理和显示 PDF 中的图像内容

## 技术架构

### 后端技术栈
- **Web 框架**: FastAPI - 现代、快速的 Python Web 框架
- **向量数据库**: Milvus - 高性能向量数据库
- **文档处理**: Marker PDF - 高质量 PDF 解析和文本提取
- **AI 模型**: 硅流 API - 提供嵌入、对话和重排序能力
- **异步处理**: 支持并发嵌入和查询处理

### 前端技术
- **模板引擎**: Jinja2
- **样式框架**: Tailwind CSS
- **交互增强**: JavaScript ES6+
- **图标库**: 自定义 SVG 图标

### 数据处理
- **文本分块**: 智能文档分割，保持语义完整性
- **元数据管理**: 支持 PDF 文件名、页码、屏蔽状态等元数据过滤
- **并发优化**: 多线程处理大量文本的向量化

## 项目结构

```
RAG/
├── app.py                 # FastAPI 主应用
├── main.py               # 命令行工具
├── config.py             # 配置管理
├── pyproject.toml        # 项目依赖
├── rag_modules/          # RAG 核心模块
│   ├── clear.py          # 数据清理
│   ├── embedding.py      # 向量嵌入
│   ├── insert.py         # 数据插入
│   ├── query.py          # 查询处理
│   ├── refer.py          # 智能检索
│   ├── reranker.py       # 结果重排序
│   └── search.py         # 搜索功能
├── utils/                # 工具模块
│   ├── chunk.py          # 文本分块
│   ├── colored_logger.py # 彩色日志
│   ├── convert.py        # 文档转换
│   └── pdf_manage.py     # PDF 管理
├── templates/            # Web 模板
├── static/              # 静态资源
├── uploads/             # 上传目录 & 答案保存
├── docs/                # 文档存储           
└── database/            # 数据库文件
```

## 快速开始

### 环境要求
- Python 3.12+
- 已安装的系统依赖（详见项目文档）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd RAG
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   # 或使用 uv
   uv sync
   ```

3. **环境配置**
   ```bash
   # 设置 API 密钥
   export siliconflow_api_key="your_api_key_here"
   ```

4. **启动服务**
   ```bash
   # Web 界面模式
   python app.py
   
   # 命令行模式
   python main.py --help
   ```

5. **访问应用**
   ```
   打开浏览器访问: http://localhost:8000
   ```

## 使用指南

### Web 界面使用

1. **上传 PDF**: 在主页面点击上传区域或拖拽 PDF 文件
2. **选择文档**: 在 PDF 列表中选择要查询的文档
3. **提问查询**: 在查询框中输入问题，支持中文
4. **查看结果**: 系统将返回基于选定文档的智能答案

### 命令行使用

```bash
# 导入 PDF 文件
python main.py --load document.pdf

# 查询问题
python main.py --query "你的问题" --include document.pdf

# 清除数据
python main.py --clear
```

### API 接口

系统提供完整的 RESTful API：

- `POST /upload-pdf` - 上传 PDF 文件
- `GET /api/pdfs` - 获取文档列表
- `POST /api/set-active-pdfs` - 设置活跃文档
- `POST /api/query` - 文档查询
- `POST /api/query/stream` - 流式查询
- `DELETE /api/clear` - 清除数据

## 高级功能

### 元数据过滤
- 支持按 PDF 文件名、页码等元数据进行过滤
- 可动态屏蔽/启用特定文档
- 详见 `docs/METADATA_FILTERING_GUIDE.md`

### 并发处理
- 支持大量文本的并发向量化
- 优化的工作线程分配
- 详见 `docs/CONCURRENT_EMBEDDING_GUIDE.md`

### 答案管理
- 自动保存查询结果到 `uploads/` 目录
- 支持 Markdown 格式的结构化答案
- 包含查询时间、使用文档等元数据

## 配置说明

主要配置项在 `config.py` 中：

- **API 配置**: 模型服务地址和密钥
- **模型配置**: 各类 AI 模型的参数设置
- **数据库配置**: Milvus 连接和集合设置
- **处理配置**: 并发线程数、相关性阈值等

## 扩展开发

### 添加新模型
1. 在 `config.py` 中添加模型配置
2. 在对应模块中实现模型调用逻辑
3. 更新相关的处理流程

### 自定义文档处理
1. 继承或修改 `utils/convert.py` 中的处理逻辑
2. 添加新的文档格式支持
3. 优化文本提取和分块策略

## 许可证

作者是菜鸡,还没学许可证相关事宜
