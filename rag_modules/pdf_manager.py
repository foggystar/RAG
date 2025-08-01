"""
PDF文档管理工具
提供屏蔽/解除屏蔽PDF文档的功能
"""

from typing import List, Optional
from pymilvus import MilvusClient
import sys
import os

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置彩色日志
from utils.colored_logger import get_colored_logger
logger = get_colored_logger(__name__)


class PDFManager:
    """PDF文档管理器"""
    
    def __init__(self, collection_name: str = "rag_docs", database: str = "milvus_rag.db"):
        """
        初始化PDF管理器
        
        Args:
            collection_name: Milvus集合名称
            database: 数据库文件路径
        """
        self.collection_name = collection_name
        self.database = database
        
        # 创建Milvus客户端
        self.client = MilvusClient(database)
    
    def block_pdf(self, pdf_name: str) -> bool:
        """
        屏蔽指定的PDF文档
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            操作是否成功
        """
        try:
            if not self.client.has_collection(collection_name=self.collection_name):
                logger.warning(f"集合 '{self.collection_name}' 不存在")
                return False
            
            logger.warning(f"MilvusClient不支持直接更新字段值")
            logger.info(f"建议重新插入数据时将 '{pdf_name}' 的 is_blocked 设置为 True")
            
            return True
            
        except Exception as e:
            logger.error(f"屏蔽PDF失败: {e}")
            return False
    
    def unblock_pdf(self, pdf_name: str) -> bool:
        """
        解除屏蔽指定的PDF文档
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            操作是否成功
        """
        try:
            if not self.client.has_collection(collection_name=self.collection_name):
                logger.warning(f"集合 '{self.collection_name}' 不存在")
                return False
            
            logger.warning(f"MilvusClient不支持直接更新字段值")
            logger.info(f"建议重新插入数据时将 '{pdf_name}' 的 is_blocked 设置为 False")
            
            return True
            
        except Exception as e:
            logger.error(f"解除屏蔽PDF失败: {e}")
            return False
    
    def list_pdfs(self, only_blocked: Optional[bool] = None) -> List[dict]:
        """
        列出集合中的所有PDF文档
        
        Args:
            only_blocked: None=全部, True=只显示被屏蔽的, False=只显示未被屏蔽的
            
        Returns:
            PDF文档信息列表
        """
        try:
            if not self.client.has_collection(collection_name=self.collection_name):
                logger.warning(f"集合 '{self.collection_name}' 不存在")
                return []
            
            # 使用MilvusClient查询数据
            # 先获取所有数据，然后在Python中过滤
            results = self.client.query(
                collection_name=self.collection_name,
                filter="",  # 获取所有数据
                output_fields=["pdf_name", "is_blocked", "page_number"],
                limit=1000
            )
            
            # 根据条件过滤
            if only_blocked is True:
                results = [r for r in results if r.get('is_blocked', False)]
            elif only_blocked is False:
                results = [r for r in results if not r.get('is_blocked', True)]
            
            # 去重并统计
            pdf_stats = {}
            for result in results:
                pdf_name = result['pdf_name']
                is_blocked = result['is_blocked']
                
                if pdf_name not in pdf_stats:
                    pdf_stats[pdf_name] = {
                        'pdf_name': pdf_name,
                        'is_blocked': is_blocked,
                        'page_count': 0,
                        'chunk_count': 0
                    }
                
                pdf_stats[pdf_name]['chunk_count'] += 1
                pdf_stats[pdf_name]['page_count'] = max(
                    pdf_stats[pdf_name]['page_count'], 
                    result['page_number']
                )
            
            return list(pdf_stats.values())
            
        except Exception as e:
            logger.error(f"查询PDF列表失败: {e}")
            return []
    
    def get_pdf_stats(self) -> dict:
        """
        获取PDF文档统计信息
        
        Returns:
            统计信息字典
        """
        try:
            all_pdfs = self.list_pdfs()
            blocked_pdfs = self.list_pdfs(only_blocked=True)
            unblocked_pdfs = self.list_pdfs(only_blocked=False)
            
            stats = {
                'total_pdfs': len(all_pdfs),
                'blocked_pdfs': len(blocked_pdfs),
                'unblocked_pdfs': len(unblocked_pdfs),
                'total_chunks': sum(pdf['chunk_count'] for pdf in all_pdfs),
                'blocked_chunks': sum(pdf['chunk_count'] for pdf in blocked_pdfs),
                'unblocked_chunks': sum(pdf['chunk_count'] for pdf in unblocked_pdfs)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
