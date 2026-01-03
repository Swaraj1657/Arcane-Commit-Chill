import os
import tempfile
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import the existing pipeline from text.py
from text import process_certificates


app = FastAPI(title="Text Extraction API", version="0.1.0")

# CORS settings – allow Vite dev server and local loopback
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/process")
async def process(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    supported_exts = {".pdf", ".jpg", ".jpeg", ".png"}
    tmp_paths: List[str] = []
    tmp_dir = tempfile.TemporaryDirectory()

    try:
        for f in files:
            ext = os.path.splitext(f.filename or "")[1].lower()
            if ext not in supported_exts:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            # Persist upload to a temp file (needed for pdf2image pipeline)
            tmp_path = os.path.join(tmp_dir.name, f.filename)
            content = await f.read()
            with open(tmp_path, "wb") as out:
                out.write(content)
            tmp_paths.append(tmp_path)

        result = process_certificates(tmp_paths)
        return JSONResponse(content=result)
    finally:
        # Cleanup temp directory and files
        try:
            tmp_dir.cleanup()
        except Exception:
            # Best-effort cleanup; ignore errors
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)