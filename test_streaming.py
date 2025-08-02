#!/usr/bin/env python3
"""
Simple test script to verify streaming functionality works correctly
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.colored_logger import get_colored_logger
from rag_modules.query import generate_answer_stream

logger = get_colored_logger(__name__)

def test_basic_streaming():
    """Test basic streaming without dependencies"""
    logger.info("Testing basic streaming functionality...")
    
    questions = ["What is the 74HC165D chip?"]
    references = ["74HC165D is an 8-bit parallel-input/serial-output shift register in a 16-pin SO16 package."]
    
    chunks = []
    try:
        for chunk in generate_answer_stream(questions, references):
            if chunk:
                chunks.append(chunk)
                print(f"Chunk {len(chunks)}: {chunk[:50]}...")
                
        full_answer = ''.join(chunks)
        logger.info(f"Streaming test completed. Total chunks: {len(chunks)}")
        logger.info(f"Full answer length: {len(full_answer)} characters")
        
        return len(chunks) > 0
        
    except Exception as e:
        logger.error(f"Streaming test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_streaming()
    if success:
        logger.info("✅ Streaming test passed!")
    else:
        logger.error("❌ Streaming test failed!")
        sys.exit(1)
