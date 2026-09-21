import os
import json
import time
import shutil
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, File, UploadFile, Request, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from paddle_extractor import extract_land_record

app = FastAPI(title="BhoomiIntelli OCR Service")

# ── CORS ────────────────────────────────────────────────────────
# Default origins: localhost dev + any *.vercel.app URL.
# Override via env var ALLOWED_ORIGINS (comma-separated) in Render/Railway dashboard.
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://*.vercel.app"
)
allowed_origins = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # catch all vercel preview URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mock Database Setup ─────────────────────────────────────
# We use /tmp in Vercel/serverless environments for writeability
is_vercel = os.getenv("VERCEL") is not None
db_path = "/tmp/db.json" if is_vercel else os.path.join(os.path.dirname(__file__), "db.json")

def read_db() -> List[Dict]:
    if not os.path.exists(db_path):
        return []
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Failed to read db.json:", e)
        return []

def write_db(data: List[Dict]):
    try:
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("Failed to write to db.json:", e)

# ── Mock DB Endpoints ──────────────────────────────────────
@app.get("/api/records")
async def get_records():
    return read_db()

@app.post("/api/records")
async def create_or_update_record(request: Request):
    new_record = await request.json()
    records = read_db()
    
    # Check if it's an update (matching id)
    record_id = new_record.get("id")
    existing_index = next((i for i, r in enumerate(records) if r.get("id") == record_id), -1)
    
    if existing_index >= 0:
        records[existing_index].update(new_record)
    else:
        records.insert(0, new_record) # Add to top
        
    write_db(records)
    return {"success": True, "record": new_record}

# ── Health Check ───────────────────────────────────────────
@app.get("/api/ocr/health")
async def health_check():
    return {
        "status": "ok",
        "service": "bhoomintelli-ocr-python",
        "version": "1.0.0",
        "paddleConfigured": True,
        "timestamp": time.time(),
    }

# ── File Upload Config ─────────────────────────────────────
uploads_dir = "/tmp/uploads" if is_vercel else os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# ── OCR Extraction Endpoint ────────────────────────────────
@app.post("/api/ocr/extract")
async def extract_ocr(document: UploadFile = File(...), hint: Optional[str] = Form(None)):
    start_time = time.time()
    
    if not document:
        raise HTTPException(status_code=400, detail="No file uploaded.")
        
    ext = os.path.splitext(document.filename)[1].lower()
    
    # Save file temporarily
    file_path = os.path.join(uploads_dir, f"{int(time.time()*1000)}{ext}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)
            
        print(f"[{'='*60}]")
        print(f"[OCR] New extraction request via PaddleOCR")
        print(f"[OCR] File: {document.filename}")
        print(f"[{'='*60}]")
        
        # Extract data using PaddleOCR
        extracted_data = extract_land_record(file_path)
        
        # Build standard response
        result = {
            "success": True,
            "data": extracted_data,
            "meta": {
                "originalFilename": document.filename,
                "totalTimeMs": int((time.time() - start_time) * 1000)
            }
        }
        
        print(f"[OCR] [SUCCESS] Extraction successful")
        print(f"[OCR] Owner: {extracted_data.get('ownerName', 'N/A')}")
        print(f"[OCR] Total time: {result['meta']['totalTimeMs']}ms\n")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"[OCR] [FAILED] Extraction failed:", str(e))
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "hint": "Internal server error during PaddleOCR extraction."
            }
        )
    finally:
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    import uvicorn
    # Optional debug run
    port = int(os.getenv("PORT", 3001))
    print(f"\n{'='*60}")
    print(f"  [OCR] BhoomiIntelli OCR Service (Python/FastAPI + PaddleOCR)")
    print(f"  [API] Running on http://localhost:{port}")
    print(f"{'='*60}\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
