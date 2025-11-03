"""Complaint generation from voice transcription"""
import google.generativeai as genai
import os
import json
import re

async def generate_complaint_from_voice(text: str) -> dict:
    """
    Generate structured complaint from voice transcription.
    Extracts title, description, category, and department.
    """
    prompt = f"""Convert this voice transcription into a structured complaint. Provide JSON:
    {{
        "title": "Brief complaint title",
        "description": "Detailed description",
        "category": "Infrastructure/Service Delivery/Corruption/Delay in Services/Quality Issues/Billing Problems/Other",
        "department": "Education/Healthcare/Transportation/Municipal Services/Police/Revenue/Agriculture/Environment/Other"
    }}
    
    Transcription: "{text}"
    """

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        
        # Try available models in order
        models_to_try = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-2.5-flash"]
        model = None
        for try_model in models_to_try:
            try:
                model = genai.GenerativeModel(try_model)
                break
            except Exception:
                continue
        if model is None:
            raise RuntimeError("Failed to initialize any Gemini model")
        response = model.generate_content(prompt)
        
        result_text = response.text
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            return json.loads(json_match.group(0))
        
        # Fallback
        return {
            "title": "Voice Complaint",
            "description": text,
            "category": "Other",
            "department": "General"
        }
    except Exception as e:
        print(f"Generation error: {e}")
        return {
            "title": "Voice Complaint",
            "description": text,
            "category": "Other",
            "department": "General"
        }

