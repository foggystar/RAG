import logging
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_colored_logger(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """获取彩色logger"""
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'main')
    
    logger = logging.getLogger(name)
    
    # 避免重复配置
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    
    return logger
