#!/usr/bin/env python3
"""
Test script for PDF deletion functionality
"""

import os
import sys
import asyncio

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_manage import get_pdf_names, delete_pdf
from utils.colored_logger import get_colored_logger
from config import Config

logger = get_colored_logger(__name__)

async def test_delete_functionality():
    """Test the PDF deletion functionality"""
    
    print("=== Testing PDF Delete Functionality ===\n")
    
    # 1. Get current PDF list
    print("1. Current PDFs in database:")
    current_pdfs = list(get_pdf_names())
    for i, pdf in enumerate(current_pdfs, 1):
        print(f"   {i}. {pdf}")
    
    if not current_pdfs:
        print("   No PDFs found in database.")
        return
    
    print(f"\nTotal PDFs: {len(current_pdfs)}\n")
    
    # 2. Test deleting a non-existent PDF
    print("2. Testing deletion of non-existent PDF:")
    non_existent_pdf = "non_existent_test_pdf"
    result = delete_pdf(non_existent_pdf)
    print(f"   Deleting '{non_existent_pdf}': {'Success' if result else 'Failed (expected)'}")
    
    # 3. Ask user which PDF to delete for testing
    if current_pdfs:
        print("\n3. Interactive deletion test:")
        print("Available PDFs for deletion test:")
        for i, pdf in enumerate(current_pdfs, 1):
            print(f"   {i}. {pdf}")
        
        try:
            choice = input(f"\nEnter PDF number to delete (1-{len(current_pdfs)}) or 'skip' to skip: ").strip()
            
            if choice.lower() != 'skip':
                pdf_index = int(choice) - 1
                if 0 <= pdf_index < len(current_pdfs):
                    pdf_to_delete = current_pdfs[pdf_index]
                    
                    confirm = input(f"\nAre you sure you want to delete '{pdf_to_delete}'? (yes/no): ").strip().lower()
                    
                    if confirm == 'yes':
                        print(f"\nDeleting '{pdf_to_delete}'...")
                        result = delete_pdf(pdf_to_delete)
                        print(f"Deletion result: {'Success' if result else 'Failed'}")
                        
                        # Check updated PDF list
                        print("\nUpdated PDF list:")
                        updated_pdfs = list(get_pdf_names())
                        for i, pdf in enumerate(updated_pdfs, 1):
                            print(f"   {i}. {pdf}")
                        print(f"Total PDFs after deletion: {len(updated_pdfs)}")
                    else:
                        print("Deletion cancelled.")
                else:
                    print("Invalid choice.")
            else:
                print("Deletion test skipped.")
                
        except (ValueError, KeyboardInterrupt):
            print("Invalid input or operation cancelled.")
    
    print("\n=== Test completed ===")

def test_database_connection():
    """Test basic database connection"""
    print("=== Testing Database Connection ===")
    
    try:
        from pymilvus import MilvusClient
        client = MilvusClient(uri=Config.DATABASE.path)
        
        print(f"Database path: {Config.DATABASE.path}")
        print(f"Collection name: {Config.DATABASE.collection_name}")
        
        # Check if collection exists
        has_collection = client.has_collection(collection_name=Config.DATABASE.collection_name)
        print(f"Collection exists: {has_collection}")
        
        if has_collection:
            stats = client.get_collection_stats(collection_name=Config.DATABASE.collection_name)
            print(f"Collection stats: {stats}")
        
        print("Database connection: Success\n")
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}\n")
        return False

if __name__ == "__main__":
    print("RAG System - PDF Deletion Test\n")
    
    # Test database connection first
    if test_database_connection():
        # Run the main test
        asyncio.run(test_delete_functionality())
    else:
        print("Cannot proceed with tests due to database connection issues.")
