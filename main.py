from rag_modules import insert, clear, refer
# from rag_modules.pdf_manager import PDFManager
from utilties import load_pdf, query
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <command> [args]")
        print("Commands: --load <pdf_name>, --clear, --query <question>, --include <pdf_name>, --split")
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
                    print("Usage: python main.py load <pdf_name>")
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
                    print("Usage: python main.py query <question>")
                    return
                # Find the next command or end of arguments for the question
                
                j = i + 1
                question_parts.append(sys.argv[j])
                if not question_parts:
                    print("Usage: python main.py query <question>")
                    return
                
                i = j + 1  # Move to next command
            case "--include":
                if i + 1 >= len(sys.argv):
                    print("Usage: python main.py include <pdf_name>")
                    return  
                pdfs.append(sys.argv[i + 1])
                # Add your include functionality here
                i += 2  # Skip the pdf_name argument
            case _:
                print(f"Unknown command: {command}")
                print("Available commands: --load, --clear, --query, --include, --split")
                i += 1

    # Load PDFs if any
    if toLoad:
        for pdf_name in toLoad:
            try:
                load_pdf.load_pdf(pdf_name)
                print(f"Loaded PDF: {pdf_name}")
            except Exception as e:
                print(f"Failed to load PDF {pdf_name}: {e}")
    if should_clear:
        clear.clear_data()
    # Process questions
    if split and question_parts:
        # Apply split to all questions at once to avoid modifying list during iteration
        original_questions = question_parts.copy()
        question_parts = []
        for question in original_questions:
            try:
                split_questions = query.split_query(question)
                if isinstance(split_questions, list):
                    question_parts.extend(split_questions)
                else:
                    # If split_query returns a string, split by newlines or keep as single question
                    question_parts.append(split_questions)
            except Exception as e:
                print(f"Failed to split question '{question}': {e}")
                question_parts.append(question)  # Keep original question if split fails
    
    for question in question_parts:
        try:
            response = query.query_to_database(question, pdfs)
            print(f"Query: {question}\n Results:")
            if response:
                for result in response:
                    print(f"PDF Name: {result['pdf_name']}, Page: {result['page_number']}, Content: {result['text'][:50]}...")
                    print("-" * 80)
            else:
                print("No results found for the query.")
        except Exception as e:
            print(f"Failed to query '{question}': {e}")


if __name__ == "__main__":
    main()
