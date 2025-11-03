from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.services.stt import transcribe_audio
import os
import shutil

router = APIRouter()

@router.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    """Basic audio transcription"""
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")

    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)

    try:
        transcribed_text = await transcribe_audio(temp_file_path)
        return {"filename": file.filename, "transcribed_text": transcribed_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@router.post("/analyze")
async def analyze_audio(text: str = Form(...)):
    """Analyze voice transcription for sentiment, urgency, and keywords"""
    try:
        # Simple fallback for now - full implementation would use AI service
        return {
            "success": True,
            "analysis": {
                "sentiment": "neutral",
                "urgency": 5,
                "keywords": [],
                "suggestedDepartment": "General",
                "priority": "Medium"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

@router.post("/generate-complaint")
async def generate_complaint(text: str = Form(...)):
    """Generate structured complaint from voice transcription"""
    try:
        # Simple fallback for now
        return {
            "success": True,
            "complaint": {
                "title": "Voice Complaint",
                "description": text,
                "category": "Other",
                "department": "General"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

@router.post("/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Enhanced transcription with full analysis and complaint generation"""
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")

    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)

    try:
        # Transcribe
        transcribed_text = await transcribe_audio(temp_file_path)
        
        # Simple analysis for now
        analysis = {
            "sentiment": "neutral",
            "urgency": 5,
            "keywords": [],
            "suggestedDepartment": "General",
            "priority": "Medium"
        }
        
        # Generate complaint
        complaint = {
            "title": "Voice Complaint",
            "description": transcribed_text,
            "category": "Other",
            "department": "General"
        }
        
        return {
            "success": True,
            "transcription": {"text": transcribed_text},
            "analysis": analysis,
            "complaint": complaint
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

