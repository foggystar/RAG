from typing import List, Dict, Any
from config import Config
from api_client import RerankClient

def get_rerank(
    query: str,
    documents: List[str],
    top_n: int = Config.DEFAULT_SEARCH_LIMIT / 2,
) -> List[Dict[str, Any]]:
    client = RerankClient()
    return client.rerank(query, documents, top_n)