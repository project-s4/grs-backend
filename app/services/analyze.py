"""Voice content analysis service using Gemini"""
import google.generativeai as genai
import os
import json
import re

async def analyze_voice_content(text: str) -> dict:
    """
    Analyze voice transcription for sentiment, urgency, and keywords.
    Returns structured analysis for complaint handling.
    """
    prompt = f"""Analyze this complaint text for grievance handling:
    
    Text: "{text}"
    
    Provide a JSON response with:
    {{
        "sentiment": "positive/negative/neutral",
        "urgency": 1-10,
        "keywords": ["key", "words"],
        "suggestedDepartment": "department name",
        "priority": "Low/Medium/High/Critical"
    }}
    
    Focus on identifying urgency, sentiment, and appropriate department."""

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
        
        analysis_text = response.text
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', analysis_text)
        if json_match:
            return json.loads(json_match.group(0))
        
        return {
            "sentiment": "neutral",
            "urgency": 5,
            "keywords": [],
            "suggestedDepartment": "General",
            "priority": "Medium"
        }
    except Exception as e:
        print(f"Analysis error: {e}")
        return {
            "sentiment": "neutral",
            "urgency": 5,
            "keywords": [],
            "suggestedDepartment": "General",
            "priority": "Medium"
        }

