import json
import re
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai

from app.config import settings
from app.constants import ComplaintCategory, UserIntent, KEYWORD_RULES

logger = logging.getLogger(__name__)


def classify_by_keywords(text: str) -> Optional[str]:
    """Fallback classification using keyword matching."""
    text_lower = text.lower()
    
    for category, keywords in KEYWORD_RULES.items():
        if any(keyword in text_lower for keyword in keywords):
            return category.value
    
    return None


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """Extract JSON from potentially markdown-wrapped response."""
    # First, try to parse as direct JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON-like structure
    json_match = re.search(r'{[^{}]*(?:{[^{}]*}[^{}]*)*}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"No valid JSON found in response: {response_text}")


def validate_and_clean_classification(classification: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean the classification response."""
    required_keys = {"category", "subcategory", "place", "department", "intent"}
    
    if not isinstance(classification, dict) or not required_keys.issubset(classification.keys()):
        raise ValueError(f"Missing required keys. Got: {list(classification.keys())}")
    
    # Validate category
    valid_categories = [c.value for c in ComplaintCategory]
    if classification["category"] not in valid_categories:
        logger.warning(f"Invalid category '{classification['category']}', defaulting to 'Other'")
        classification["category"] = ComplaintCategory.OTHER.value
        classification["subcategory"] = "General"
    
    # Validate intent
    valid_intents = [i.value for i in UserIntent]
    if classification["intent"] not in valid_intents:
        logger.warning(f"Invalid intent '{classification['intent']}', defaulting to 'other'")
        classification["intent"] = UserIntent.OTHER.value
    
    # Clean string fields
    for key in ["place", "department", "subcategory"]:
        if not classification[key] or not isinstance(classification[key], str) or classification[key].strip() == "":
            classification[key] = "Unknown" if key != "subcategory" else "General"
    
    return classification


async def classify_complaint(text: str) -> str:
    """Classify complaint text using Gemini AI with robust error handling."""
    try:
        # Configure Gemini
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=settings.gemini_api_key)
        
        # Use a valid model with fallback chain
        # Try models in order: configured -> gemini-2.0-flash -> gemini-flash-latest -> gemini-2.5-flash
        model_name = settings.gemini_model_name or "gemini-2.0-flash"
        fallback_models = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
        
        model = None
        last_error = None
        
        # Try configured model first
        models_to_try = [model_name] + [m for m in fallback_models if m != model_name]
        
        for try_model in models_to_try:
            try:
                model = genai.GenerativeModel(try_model)
                logger.info(f"Successfully initialized Gemini model: {try_model}")
                break
            except Exception as model_error:
                last_error = model_error
                logger.warning(f"Model {try_model} not available: {model_error}")
                continue
        
        if model is None:
            raise RuntimeError(f"Failed to initialize any Gemini model. Last error: {last_error}")
        
        # Create prompt
        categories_list = ", ".join([f'"{c.value}"' for c in ComplaintCategory])
        intents_list = ", ".join([f'"{i.value}"' for i in UserIntent])
        
        prompt = f"""
You are a complaint classification system. Analyze the following text and respond with ONLY a JSON object.

Text: "{text}"

Classify into:
1. category: One of [{categories_list}]
   - Sanitation: Garbage, waste, dead animals, cleaning issues, trash collection, animal carcasses
   - Water Supply: Water issues, tap water, supply problems, quality issues
   - Street Lighting: Street lights, lamps, electrical poles, illumination, bulbs
   - Roads: Road conditions, potholes, construction, footpaths, sidewalks
   - Public Safety: Crime, security, police-related issues, emergencies
   - Other: Anything that doesn't fit the above categories
2. subcategory: Specific subcategory or "General" if unclear
3. place: Location mentioned or "Unknown" if none
4. department: Government department involved or "Unknown" if none  
5. intent: One of [{intents_list}]

IMPORTANT: Dead animals, carcasses, rotting organic matter, and disposal of deceased animals should ALWAYS be classified as "Sanitation" category.

Respond with ONLY this JSON structure, no markdown, no explanation:
{{
    "category": "<category>",
    "subcategory": "<subcategory>",
    "place": "<place>",
    "department": "<department>",
    "intent": "<intent>"
}}"""
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        raw_output = response.text.strip()
        
        logger.info(f"Gemini raw response: {raw_output}")
        
        # Extract and validate JSON
        classification = extract_json_from_response(raw_output)
        classification = validate_and_clean_classification(classification)
        
        logger.info(f"Successfully classified: {classification}")
        return json.dumps(classification)
        
    except Exception as e:
        logger.error(f"Gemini classification failed: {e}")
        
        # Try keyword-based fallback
        fallback_category = classify_by_keywords(text)
        if fallback_category:
            logger.info(f"Using keyword fallback: {fallback_category}")
            return json.dumps({
                "category": fallback_category,
                "subcategory": "General",
                "place": "Unknown",
                "department": "Unknown",
                "intent": "complaint"
            })
        
        # Final fallback
        logger.warning("Using final fallback classification")
        return json.dumps({
            "category": ComplaintCategory.OTHER.value,
            "subcategory": "General", 
            "place": "Unknown",
            "department": "Unknown",
            "intent": UserIntent.OTHER.value
        })

