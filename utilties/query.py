import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from openai import OpenAI

# Add parent directory to path when running this file directly
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_modules import refer

def split_query(
    query: str, 
    model: str = "Qwen/Qwen3-30B-A3B",
    api_key: Optional[str] = None
) -> List[str]:
    
    if api_key is None:
        api_key = os.getenv('siliconflow_api_key')
        if not api_key:
            raise ValueError("API key not found. Please set siliconflow_api_key environment variable.")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Split the query into 2-3 sub-questions. Output only the questions, one per line."},
                {"role": "user", "content": query}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        if content:
            questions = [line.strip() for line in content.split('\n') if line.strip()]
            return questions[:3] if questions else [query]
        return [query]
    
    except Exception as e:
        print(f"Warning: Failed to split query: {e}")
        return [query]


def query_to_database(question: str, pdfs: list[str]) -> List[dict]:
    results = refer.get_reference_with_filter(question, included_pdfs=pdfs, limit=5)
    return results if results else []

if __name__ == "__main__":
    # Test the import
    print("Testing query module...")
    
    # Test split_query function
    test_query = "What is the capital of France?"
    print(f"Testing split_query with: '{test_query}'")
    
    try:
        result = split_query(test_query)
        print(f"Split result: {result}")
    except ValueError as e:
        print(f"Note: {e}")
        print("This is expected if you haven't set up the API key.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    print("\nModule loaded successfully!")