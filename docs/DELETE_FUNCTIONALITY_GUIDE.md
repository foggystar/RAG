# PDF删除功能说明

## 功能概述

本功能允许用户选择特定的PDF文件进行删除，包括删除数据库中的相关数据和物理文件。

## 实现细节

### 1. 后端实现

#### `utils/pdf_manage.py` 中的 `delete_pdf()` 函数

```python
def delete_pdf(pdf_name: str):
    """
    删除特定PDF及其关联数据
    
    Args:
        pdf_name: 要删除的PDF名称（不含扩展名）
    
    Returns:
        bool: 成功返回True，失败返回False
    """
```

**实现特点：**
- 使用Milvus客户端连接数据库
- 通过过滤器删除数据库中的相关记录：`filter=f'pdf_name == "{pdf_name}"'`
- 同时删除物理文件（uploads目录和docs目录中的处理文件）
- 完整的错误处理和日志记录

#### `app.py` 中的API端点

```python
@app.delete("/api/pdfs/{pdf_name}")
async def delete_pdf_endpoint(pdf_name: str):
```

**功能特点：**
- RESTful API设计，使用DELETE方法
- 路径参数接收PDF名称
- 自动从活跃PDF列表中移除被删除的PDF
- 返回标准化的API响应格式

### 2. 前端实现

#### HTML界面更新
- 为每个PDF项目添加删除按钮（🗑️）
- 改进的布局，使用flex布局对齐复选框、标签和删除按钮
- 悬停效果提升用户体验

#### JavaScript功能
- `deletePdf(pdfName)` 函数处理删除操作
- 删除前确认对话框
- 删除成功后自动刷新PDF列表
- 从活跃PDF列表中移除已删除的PDF

## 使用方法

### 1. 通过Web界面删除

1. 打开RAG系统主页
2. 在"Imported PDFs"部分找到要删除的PDF
3. 点击PDF右侧的🗑️按钮
4. 在确认对话框中点击"确定"
5. 系统将删除PDF及其所有关联数据

### 2. 通过API删除

```bash
curl -X DELETE "http://localhost:8000/api/pdfs/your_pdf_name"
```

### 3. 测试删除功能

运行测试脚本：
```bash
python test_delete_pdf.py
```

## 删除内容

删除操作将移除以下内容：

1. **数据库记录**：
   - 文档向量
   - 文本内容
   - 页面信息
   - 所有相关元数据

2. **物理文件**：
   - `uploads/` 目录中的原始PDF文件
   - `docs/` 目录中的处理后文件夹
   - `uploads/` 目录中的处理文件夹（如果存在）

## 安全特性

1. **确认机制**：删除前需要用户确认
2. **错误处理**：详细的错误信息和日志记录
3. **状态同步**：自动更新活跃PDF列表
4. **路径安全**：使用URL编码处理PDF名称

## 注意事项

1. **不可逆操作**：删除操作不可逆，请谨慎使用
2. **文件清理**：系统会尝试删除相关物理文件，但即使文件删除失败，数据库删除操作仍会成功
3. **活跃状态**：如果删除的PDF当前处于活跃状态，系统会自动将其从活跃列表中移除
4. **并发安全**：支持多用户环境下的安全删除操作

## 技术细节

### Milvus删除操作

使用Milvus的过滤删除功能：
```python
res = client.delete(
    collection_name=Config.DATABASE.collection_name,
    filter=f'pdf_name == "{pdf_name}"'
)
```

这种方式比传统的先查询再删除更高效，直接通过过滤条件删除所有匹配的记录。

### 错误处理

- 数据库连接失败
- PDF不存在
- 文件系统权限问题
- 网络通信错误

所有错误都有相应的处理机制和用户友好的错误信息。

## 扩展功能

未来可以考虑添加：
1. 批量删除功能
2. 回收站机制
3. 删除历史记录
4. 权限控制
5. 删除预览（显示将被删除的内容）
