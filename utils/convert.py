import os
import subprocess

from config import Config
from utils.colored_logger import get_colored_logger

logger = get_colored_logger(__name__)

def pdf2md(
        pdf_path: str,
        output_dir: str
):
    # Set the model cache directory
    logger.info(f"Loading models from {Config.MODEL_DIR}")
    os.environ['MODEL_CACHE_DIR'] = Config.MODEL_DIR
    
    # Run the marker_single command
    logger.info(f"Starting PDF to Markdown conversion: {pdf_path}")
    logger.info(f"Output directory: {output_dir}")
    
    # Use Popen to get real-time output
    process = subprocess.Popen([
        'marker_single', 
        pdf_path, 
        '--output_dir', 
        output_dir
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
    
    # Read output line by line in real-time
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            # Log each line of output as it comes
            logger.info(f"[marker_single] {output.strip()}")
    
    # Wait for the process to complete and get return code
    return_code = process.poll()
    
    if return_code == 0:
        logger.info("PDF to Markdown conversion completed successfully")
    else:
        logger.error(f"PDF to Markdown conversion failed with return code: {return_code}")
        raise RuntimeError(f"marker_single failed with return code: {return_code}")

if __name__ == "__main__":
    pdf2md("../docs/74HC165D.pdf", "../docs/")