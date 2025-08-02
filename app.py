"""
FastAPI web application for RAG (Retrieval-Augmented Generation) system.
Provides a user-friendly web interface for PDF management and querying.
"""

import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import RAG modules
from utils.pdf_manage import get_pdf_names, insert_pdf, set_active_pdfs, query_pdfs_async, query_pdfs_stream_async
from rag_modules.clear import clear_database
from utils.colored_logger import get_colored_logger

logger = get_colored_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="RAG System", description="PDF-based Retrieval-Augmented Generation System")

# Create necessary directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("docs", exist_ok=True)  # Ensure docs directory exists

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/docs", StaticFiles(directory="docs"), name="docs")  # Add docs directory for images
templates = Jinja2Templates(directory="templates")

# Global state for active PDFs (in production, use session management)
active_pdfs = []

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    active_pdfs: List[str]

class SetActivePDFsRequest(BaseModel):
    pdf_names: List[str]

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page with all RAG functionalities"""
    try:
        pdf_list = list(get_pdf_names())
        return templates.TemplateResponse("index.html", {
            "request": request,
            "pdf_list": pdf_list,
            "active_pdfs": active_pdfs
        })
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return HTMLResponse(f"<h1>Error loading page: {e}</h1>", status_code=500)

# 1. Import PDF functionality
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file
        upload_path = os.path.join("uploads", file.filename)
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the PDF
        success = insert_pdf(upload_path)
        
        if success:
            return APIResponse(
                success=True, 
                message=f"Successfully uploaded and processed {file.filename}",
                data={"filename": file.filename}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to process PDF")
            
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. List imported PDFs functionality  
@app.get("/api/pdfs")
async def list_pdfs():
    """Get list of all imported PDF names"""
    try:
        pdf_names = list(get_pdf_names())
        return APIResponse(
            success=True,
            message="Retrieved PDF list successfully",
            data={"pdfs": pdf_names}
        )
    except Exception as e:
        logger.error(f"Error getting PDF list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. Set active PDFs functionality
@app.post("/api/set-active-pdfs")
async def set_active_pdfs_endpoint(request: SetActivePDFsRequest):
    """Set which PDFs should be currently used for querying"""
    try:
        global active_pdfs
        active_pdfs = request.pdf_names
        success = set_active_pdfs(request.pdf_names)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Successfully set {len(request.pdf_names)} PDFs as active",
                data={"active_pdfs": request.pdf_names}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to set active PDFs")
            
    except Exception as e:
        logger.error(f"Error setting active PDFs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. Query functionality
@app.post("/api/query")
async def query_endpoint(request: QueryRequest):
    """Answer user's question based on selected PDFs"""
    try:
        if not request.active_pdfs:
            raise HTTPException(status_code=400, detail="No PDFs selected for querying")
        
        answer = await query_pdfs_async(request.query, request.active_pdfs)
        
        return APIResponse(
            success=True,
            message="Query processed successfully",
            data={
                "query": request.query,
                "answer": answer,
                "used_pdfs": request.active_pdfs
            }
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4.1. Streaming Query functionality
@app.post("/api/query/stream")
async def query_stream_endpoint(request: QueryRequest):
    """Stream answer for user's question based on selected PDFs"""
    try:
        if not request.active_pdfs:
            raise HTTPException(status_code=400, detail="No PDFs selected for querying")
        
        async def generate_stream():
            try:
                async for chunk in query_pdfs_stream_async(request.query, request.active_pdfs):
                    if chunk:
                        # Ensure proper SSE format
                        yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"  # Signal completion
            except Exception as e:
                logger.error(f"Error in stream generation: {e}")
                yield f"data: Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    except Exception as e:
        logger.error(f"Error processing streaming query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. Clear database functionality
@app.delete("/api/clear")
async def clear_all_data():
    """Clear all imported PDFs from the database"""
    try:
        clear_database()
        global active_pdfs
        active_pdfs = []
        
        return APIResponse(
            success=True,
            message="Successfully cleared all data from database"
        )
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "RAG system is running"}

# Test endpoint for checking image accessibility
@app.get("/test-images")
async def test_images():
    """Test endpoint to list available images"""
    try:
        images = []
        docs_path = "docs"
        if os.path.exists(docs_path):
            for root, dirs, files in os.walk(docs_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        rel_path = os.path.relpath(os.path.join(root, file), docs_path)
                        images.append({
                            "filename": file,
                            "path": f"/docs/{rel_path}",
                            "full_path": os.path.join(root, file)
                        })
        
        return APIResponse(
            success=True,
            message=f"Found {len(images)} images",
            data={"images": images}
        )
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        return APIResponse(
            success=False,
            message=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)