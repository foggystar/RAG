from typing import List, Dict, Optional, Any
from . import reranker, search
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def get_reference(
        query: str,
        included_pdfs: List[str]
) -> List[Dict[str, Any]]:
    pass