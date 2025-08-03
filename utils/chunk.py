import json
import os
from typing import List, Dict, Any

from config import Config
from utils.colored_logger import get_colored_logger

logger = get_colored_logger(__name__)

def chunk_with_metadata(markdown_content: str, metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    chunks = []
    
    # 过滤掉重复的标题和页眉页脚
    filtered_meta = []
    seen_titles = set()
    for item in metadata:
        title = item['title']
        # 跳过重复标题和页眉页脚
        if (title not in seen_titles):
            filtered_meta.append({
                'title': item['title'],
                'page_id': item['page_id']
            })
            seen_titles.add(title)
        
    # print(f"Filtered TOC: {filtered_meta}")
    start_index = 0
    end_index = 0
    chunks = []
    for i, toc_item in enumerate(filtered_meta):
        start_index = markdown_content.find(toc_item['title'])
        end_index = markdown_content.find(filtered_meta[i+1]['title']) if (i + 1) < len(filtered_meta) else len(markdown_content)
        
        if len(markdown_content[start_index:end_index].strip()) < 50:
            logger.warning(f"Skipping chunk for '{toc_item['title']}' due to insufficient content length")
            continue
        
        current_pos = start_index
        while current_pos < end_index:
            chunk_end = min(current_pos + Config.DATABASE.chunk_size_limit, end_index)
            chunk_content = markdown_content[current_pos:chunk_end].strip()
            
            # 只有当chunk内容长度大于0时才添加
            if chunk_content:
                chunks.append({
                    'content': chunk_content,
                    'metadata': {
                        'title': toc_item['title'],
                        'page_id': toc_item['page_id']+1
                    }
                })
            current_pos = chunk_end
    
    return chunks

def load_and_chunk(markdown_path: str, metadata_path: str) -> List[Dict[str, Any]]:
    """
    加载文件并进行分块的便捷函数
    
    Args:
        markdown_path: markdown文件路径
        metadata_path: metadata JSON文件路径
    
    Returns:
        List[Dict]: 分块结果
    """
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
        # print(markdown_content[:100])
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        # print(metadata['table_of_contents'])
    return chunk_with_metadata(markdown_content, metadata['table_of_contents'])


if __name__ == "__main__":
    # 示例用法
    markdown_path = "../docs/74HC165D/74HC165D.md"
    metadata_path = "../docs/74HC165D/74HC165D_meta.json"
    
    load_and_chunk(markdown_path, metadata_path)
    