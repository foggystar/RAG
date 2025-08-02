from rag_modules import clear, query
# from rag_modules.pdf_manager import PDFManager
from utils import convert
from utils.colored_logger import get_colored_logger
import sys
import logging

# 设置彩色日志
logger = get_colored_logger(__name__)

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py <command> [args]")
        logger.error("Commands: --load <pdf_name>, --clear, --query <question>, --include <pdf_name>, --split")
        return
    pdfs=[]
    question_parts = []
    toLoad = []
    should_clear = False
    split = False
    # Process each command in sequence
    i = 1

    while i < len(sys.argv):
        command = sys.argv[i]
        
        match command:
            case "--load":
                if i + 1 >= len(sys.argv):
                    logger.error("Usage: python main.py load <pdf_name>")
                    return
                pdf_name = sys.argv[i + 1]
                toLoad.append(pdf_name)
                i += 2  # Skip the pdf_name argument
            case "--clear":
                should_clear = True
                i += 1
            case "--split":
                split = True
                i += 1
            case "--query":
                if i + 1 >= len(sys.argv):
                    logger.error("Usage: python main.py query <question>")
                    return
                # Find the next command or end of arguments for the question
                
                j = i + 1
                question_parts.append(sys.argv[j])
                if not question_parts:
                    logger.error("Usage: python main.py query <question>")
                    return
                
                i = j + 1  # Move to next command
            case "--include":
                if i + 1 >= len(sys.argv):
                    logger.error("Usage: python main.py include <pdf_name>")
                    return  
                pdfs.append(sys.argv[i + 1])
                # Add your include functionality here
                i += 2  # Skip the pdf_name argument
            case _:
                logger.error(f"Unknown command: {command}")
                logger.error("Available commands: --load, --clear, --query, --include, --split")
                i += 1

    # Load PDFs if any
    if toLoad:
        for pdf_name in toLoad:
            try:
                convert.load_pdf(pdf_name)
                logger.info(f"Loaded PDF: {pdf_name}")
            except Exception as e:
                logger.error(f"Failed to load PDF {pdf_name}: {e}")
    if should_clear:
        clear.clear_data()
    # Process questions
    split_questions = query.split_query(question_parts)
    
    response = []
    for question in split_questions:
        try:
            logger.info(f"Querying: {question}")
            response.append(query.query_to_database(question, pdfs))
            # print(f"Query: {question}\n Results:")
            
        except Exception as e:
            logger.error(f"Failed to query '{question}': {e}")

    if response:
        print(query.generate_answer(split_questions, response))
    else:
        logger.warning("No results found for the query.")


if __name__ == "__main__":
    main()
