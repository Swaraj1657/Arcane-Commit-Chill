"""
FastAPI server for certificate verification
"""
import os
import sys
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import tempfile
import shutil

# Add parent directory to path to import text processing modules
sys.path.insert(0, str(Path(__file__).parent))

from text import process_certificates
from map_to_schema import map_processing_result_to_schema

app = FastAPI(title="Certificate Verification API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Certificate Verification API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/verify-certificate")
async def verify_certificate(file: UploadFile = File(...)):
    """
    Upload and verify a certificate document.
    Returns the processed verification results.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the certificate
        print(f"Processing certificate: {file.filename}")
        result = process_certificates([temp_file_path])
        
        # Determine document type from filename or content
        doc_type = "DEGREE"  # Default
        filename_lower = file.filename.lower()
        if "marksheet" in filename_lower or "mark" in filename_lower:
            doc_type = "MARKSHEET"
        elif "internship" in filename_lower:
            doc_type = "INTERNSHIP"
        elif "course" in filename_lower or "certificate" in filename_lower:
            doc_type = "COURSE"
        
        # Map to database schema
        mapped_result = map_processing_result_to_schema(result, doc_type)
        
        # Return both the mapped result and full processing result
        return JSONResponse(content={
            "mapped_data": mapped_result,
            "full_processing_result": result
        })
    
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error processing certificate: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing certificate: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp files: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

