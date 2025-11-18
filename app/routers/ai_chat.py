from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.ai_chat import ChatMessage, ChatResponse
from app.schemas.complaints import ComplaintCreate
from app.services.stt import transcribe_audio
from app.services.translate import translate_text
from app.services.classify import classify_complaint
from app.services.map import map_department
from app.routers.ai import ai_create_complaint_internal
from app.db.session import get_db
from app.config import settings
from langdetect import detect, LangDetectException
from typing import Tuple
import json
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter()

# simple in-memory context (replace with Redis in prod)
SESSION_CONTEXT = {}

QUESTIONS = {
    "user.phone": "Please provide your phone number (10 digits):",
    "location": "Please share the location of the issue (street/area):",
    "department_code": "Which department should handle this? 1. Sanitation 2. Water Supply 3. Street Lighting",
    "confirmation": ""
}


def validate_phone_number(phone: str) -> bool:
    """Validate phone number is 10 digits"""
    # Remove spaces, dashes, and other common formatting
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's exactly 10 digits
    return bool(re.match(r'^\d{10}$', cleaned))

def validate_description(description: str) -> Tuple[bool, str]:
    """Validate description is meaningful (not just short gibberish)"""
    description = description.strip()
    
    # Too short (less than 5 characters after cleaning)
    if len(description) < 5:
        return False, "Your description is too short. Please provide more details about your complaint (at least 5 characters)."
    
    # Only common greeting words or single characters
    greeting_words = ['hi', 'hello', 'hey', 'hu', 'hjh', 'ok', 'yes', 'no', 'y', 'n']
    words = description.lower().split()
    if len(words) == 1 and words[0] in greeting_words:
        return False, "That doesn't seem like a complaint description. Please describe the issue you're facing (e.g., 'There is garbage on my street' or 'Water supply is not working')."
    
    # Multiple very short words that look like incomplete input
    if len(words) <= 3 and all(len(word) <= 3 for word in words):
        return False, "Your description seems incomplete. Please provide more details about your complaint."
    
    return True, ""

def detect_intent_basic(text: str) -> str:
    """Basic intent detection using pattern matching for greetings/thanks."""
    text_lower = text.lower().strip()
    
    # Check for very short/incomplete input first
    if len(text_lower) <= 3:
        # Check if it's a known greeting
        if text_lower in ['hi', 'hu', 'hii', 'hai', 'hlo', 'hey', 'ok']:
            return "greeting"
        # Otherwise, likely incomplete input that needs clarification
        return "incomplete"
    
    # Greeting patterns
    greeting_patterns = [
        r'^(hi|hello|hey|greetings|namaste|good morning|good afternoon|good evening|hii|hai|hlo|hellow)',
        r'^(hi\s+(there|this)\s+)',
    ]
    
    # Thanks/acknowledgment patterns  
    thanks_patterns = [
        r'^(thanks|thank you|thankyou|thnx|thank u|tysm|appreciate|grateful)',
        r'^(thank\s+(you|so much))',
        r'^(thanks\s+(a lot|very much))',
    ]
    
    # Query patterns (asking questions)
    query_patterns = [
        r'\b(what|how|when|where|who|why|can you|could you|is|are|do|does|will)\b',
        r'\b(status|track|check|know|tell me|information|info)\b',
        r'\?\s*$',  # Ends with question mark
    ]
    
    # Suggestion patterns
    suggestion_patterns = [
        r'\b(suggest|suggestion|recommend|improve|better|should|could)\b',
        r'\b(idea|proposal|feedback)\b',
    ]
    
    # Request patterns (different from complaints - asking for services)
    request_patterns = [
        r'\b(request|need|want|require|apply|application|form|service)\b',
        r'\b(can i|may i|i would like|please provide)\b',
    ]
    
    # Check for greetings
    for pattern in greeting_patterns:
        if re.match(pattern, text_lower):
            return "greeting"
    
    # Check for thanks
    for pattern in thanks_patterns:
        if re.match(pattern, text_lower):
            return "thanks"
    
    # Check for queries
    if len(text_lower) > 5:  # Only check queries for longer text
        for pattern in query_patterns:
            if re.search(pattern, text_lower):
                return "query"
    
    # Check for suggestions
    for pattern in suggestion_patterns:
        if re.search(pattern, text_lower):
            return "suggestion"
    
    # Check for requests
    for pattern in request_patterns:
        if re.search(pattern, text_lower):
            return "request"
    
    # Check if it's too short or seems like incomplete speech
    words = text.split()
    if len(words) <= 3:
        # Common greeting words
        if any(word.lower() in ['hi', 'hello', 'hey', 'namaste', 'hii', 'hai', 'hlo', 'hu', 'hjh'] for word in words):
            return "greeting"
        # Common thanks words
        if any(word.lower() in ['thanks', 'thank', 'thnx', 'thanku'] for word in words):
            return "thanks"
    
    # Otherwise, default to complaint (will be refined by AI classification)
    return "complaint"

@router.post("/chat", response_model=ChatResponse)
async def chatbot(msg: ChatMessage, db: Session = Depends(get_db)):
    session = SESSION_CONTEXT.get(msg.session_id, {})

    # Step 0. Check for greetings/thanks/other intents ONLY if not in active complaint flow
    # Skip this check if we're already collecting complaint data
    is_active_complaint = "description" in session or "awaiting_field" in session
    
    if not is_active_complaint:
        # First use basic pattern matching
        basic_intent = detect_intent_basic(msg.user_input)
        
        # Handle incomplete input
        if basic_intent == "incomplete":
            SESSION_CONTEXT[msg.session_id] = session
            return ChatResponse(
                message="I didn't quite understand that. Could you please provide more details? For example:\n• 'There is garbage on my street'\n• 'Water supply is not working'\n• 'Street lights are broken'\n\nOr if you have a question, feel free to ask!",
                is_ready=False,
                context=session
            )
        
        # Handle greetings
        if basic_intent == "greeting":
            greeting_responses = [
                "Hello! 👋 I'm the GRS Assistant. I can help you with:\n• Filing complaints\n• Checking complaint status\n• Providing information\n• Taking suggestions\n\nHow can I assist you today?",
                "Hi there! I'm here to help with your grievances and queries. What would you like to do?",
                "Welcome! I can help you file complaints, check status, or answer questions. How can I assist?"
            ]
            SESSION_CONTEXT[msg.session_id] = session
            return ChatResponse(
                message=greeting_responses[0],
                is_ready=False,
                context=session
            )
        
        # Handle thanks
        if basic_intent == "thanks":
            thanks_responses = [
                "You're very welcome! 😊 Is there anything else I can help you with?",
                "Glad I could help! Feel free to reach out if you need any further assistance.",
                "Happy to assist! Let me know if you have any other concerns."
            ]
            SESSION_CONTEXT[msg.session_id] = session
            return ChatResponse(
                message=thanks_responses[0],
                is_ready=False,
                context=session
            )
        
        # For other intents, use AI classification to get more accurate intent
        # But handle queries and suggestions immediately without complaint flow
        if basic_intent in ["query", "suggestion", "request"]:
            # Use AI to classify and get intent
            try:
                classification_raw = await classify_complaint(msg.user_input)
                classification = json.loads(classification_raw)
                ai_intent = classification.get("intent", basic_intent)
                
                # Handle queries (status checks, information requests)
                if ai_intent == "query" or basic_intent == "query":
                    query_responses = [
                        "I can help you with information about the grievance system. You can:\n• File a complaint by describing your issue\n• Check complaint status (provide reference number)\n• Get department information\n\nWhat information do you need?",
                        "I'd be happy to help with your query! You can ask me about:\n• How to file a complaint\n• Complaint tracking\n• Department details\n• System features\n\nWhat would you like to know?",
                    ]
                    # Check if it's a status query
                    if re.search(r'\b(status|track|reference|complaint number|tracking id)\b', msg.user_input.lower()):
                        SESSION_CONTEXT[msg.session_id] = session
                        return ChatResponse(
                            message="To check your complaint status, please provide your reference number (e.g., COMP-123456). You can also file a new complaint by describing your issue.",
                            is_ready=False,
                            context=session
                        )
                    SESSION_CONTEXT[msg.session_id] = session
                    return ChatResponse(
                        message=query_responses[0],
                        is_ready=False,
                        context=session
                    )
                
                # Handle suggestions
                if ai_intent == "suggestion" or basic_intent == "suggestion":
                    suggestion_responses = [
                        "Thank you for your suggestion! I appreciate your feedback. While I currently help with filing complaints, I'll note your suggestion for the system administrators.\n\nWould you like to file a complaint or need any other assistance?",
                        "I value your suggestion! However, I'm currently focused on helping with grievances and complaints. Your feedback will be considered.\n\nIs there anything else I can help with?",
                    ]
                    SESSION_CONTEXT[msg.session_id] = session
                    return ChatResponse(
                        message=suggestion_responses[0],
                        is_ready=False,
                        context=session
                    )
                
                # Handle requests (service applications, forms)
                if ai_intent == "request" or basic_intent == "request":
                    request_responses = [
                        "I can help you file a complaint about the service or issue you're requesting. Please describe what you need, and I'll assist you in filing it with the appropriate department.\n\nFor applications and forms, you may need to visit the department directly or their website.",
                        "I can help you file a complaint related to your request. Please describe the issue, and I'll categorize it and route it to the right department.\n\nNote: For service applications, you might need to contact the department directly.",
                    ]
                    SESSION_CONTEXT[msg.session_id] = session
                    return ChatResponse(
                        message=request_responses[0],
                        is_ready=False,
                        context=session
                    )
            except Exception as e:
                logger.error(f"Error in AI classification for intent detection: {e}")
                # Fall through to complaint handling if AI fails

    # Step 1. Update with new user input if answering a missing question
    if "awaiting_field" in session:
        field = session["awaiting_field"]
        
        # Validate input based on field type
        if field == "user.phone":
            # Validate phone number
            if not validate_phone_number(msg.user_input):
                SESSION_CONTEXT[msg.session_id] = session
                return ChatResponse(
                    message="⚠️ Invalid phone number. Please provide a valid 10-digit phone number (e.g., 9876543210).",
                    missing_fields=["user.phone"],
                    is_ready=False,
                    context=session
                )
            # Clean and store phone number
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', msg.user_input)
            session[field] = cleaned_phone
            session.pop("awaiting_field")
        elif field == "location":
            # Validate location is meaningful
            if len(msg.user_input.strip()) < 3:
                SESSION_CONTEXT[msg.session_id] = session
                return ChatResponse(
                    message="⚠️ Please provide a more specific location (e.g., 'Main Street, Area Name' or 'Near XYZ School').",
                    missing_fields=["location"],
                    is_ready=False,
                    context=session
                )
            session[field] = msg.user_input.strip()
            session.pop("awaiting_field")
        elif field == "confirmation":
            user_response = msg.user_input.lower()
            if user_response in ["yes", "y", "confirm", "correct"]:
                session["confirmed"] = True
                session.pop("awaiting_field")
            else:
                # User provided more details or correction, append to description
                new_info = msg.user_input
                session["description"] += f"\nUser added: {new_info}"
                
                # Re-classify the complaint with the updated description
                try:
                    full_description = session.get("description", "")
                    logger.info(f"Re-classifying complaint with updated description: {full_description[:100]}")
                    
                    classification_raw = await classify_complaint(full_description)
                    classification = json.loads(classification_raw)
                    
                    # Update category and subcategory
                    old_category = session.get("category")
                    session["category"] = classification.get("category", session.get("category"))
                    session["subcategory"] = classification.get("subcategory", session.get("subcategory"))
                    
                    # Re-map department based on new category
                    mapped_dept = map_department(session["category"], db)
                    if mapped_dept:
                        session["department_code"] = mapped_dept
                    
                    logger.info(f"Updated classification - Category: {session['category']}, Department: {session['department_code']}")
                    
                    # Show updated confirmation with changes highlighted
                    if old_category != session["category"]:
                        confirmation_message = (
                            f"Updated complaint based on new details:\n"
                            f"📝 Description: {session['description']}\n"
                            f"🏷️ Category: {session['category']} (updated)\n"
                            f"📍 Location: {session.get('location', 'N/A')}\n"
                            f"📞 Phone: {session.get('user.phone', 'N/A')}\n\n"
                            f"Does this look correct now? (Yes/No, or add more details)"
                        )
                        session["awaiting_field"] = "confirmation"
                        SESSION_CONTEXT[msg.session_id] = session
                        return ChatResponse(
                            message=confirmation_message,
                            missing_fields=[],
                            is_ready=False,
                            context=session
                        )
                except Exception as e:
                    logger.error(f"Error re-classifying complaint: {e}")
                
                # Keep awaiting_field as confirmation to re-ask
        else:
            # For other fields, just store the value
            session[field] = msg.user_input
            session.pop("awaiting_field")

    # Step 2. If description not set, classify and handle initial user data
    if "description" not in session:
        text = msg.user_input
        
        # Validate description quality before proceeding
        is_valid, error_msg = validate_description(text)
        if not is_valid:
            SESSION_CONTEXT[msg.session_id] = session
            return ChatResponse(
                message=error_msg,
                is_ready=False,
                context=session
            )
        
        session["raw_text"] = text
        try:
            language = detect(text)
        except LangDetectException:
            logger.warning("Could not detect language for user input; defaulting to 'unknown'")
            language = "unknown"
        session["language"] = language
        translated = translate_text(text, "en") if text.strip() else ""
        if not translated:
            translated = text
        session["description"] = translated

        classification_raw = await classify_complaint(translated)
        try:
            classification = json.loads(classification_raw)
        except:
            classification = {}

        # Store the AI-detected intent
        ai_intent = classification.get("intent", "complaint")
        session["intent"] = ai_intent
        
        # Only proceed with complaint flow if intent is actually a complaint
        if ai_intent not in ["complaint", "other"]:
            # This shouldn't happen here as we handle queries/suggestions above
            # But just in case, handle it
            if ai_intent == "query":
                SESSION_CONTEXT[msg.session_id] = session
                return ChatResponse(
                    message="I can help with information about complaints. Please describe your specific question, or provide a reference number to check status.",
                    is_ready=False,
                    context=session
                )
        
        session["category"] = classification.get("category")
        session["subcategory"] = classification.get("subcategory")
        # Map category to department code (Sanitation -> BBMP, Street Lighting -> BESCOM for Bengaluru)
        mapped_dept = map_department(session["category"], db) 
        session["department_code"] = mapped_dept or "PW"  # Default fallback to Public Works
    
    # Handle initial user data if provided
    if msg.user:
            if msg.user.get("phone"):
                session["user.phone"] = msg.user["phone"]
            if msg.user.get("location"):
                session["location"] = msg.user["location"]

    # Step 3. Check missing fields
    missing = []
    if "user.phone" not in session: missing.append("user.phone")
    if "location" not in session: missing.append("location")
    if not session.get("department_code"): missing.append("department_code")

    if missing:
        field = missing[0]
        session["awaiting_field"] = field
        SESSION_CONTEXT[msg.session_id] = session
        return ChatResponse(
            message=QUESTIONS[field],
            missing_fields=missing,
            is_ready=False,
            context=session
        )

    # Step 4. All data ready, now ask for confirmation if not already confirmed
    if not session.get("confirmed"):
        confirmation_message = (
            f"Please review your complaint:\n"
            f"Description: {session['description']}\n"
            f"Category: {session['category']}\n"
            f"Location: {session.get('location', 'N/A')}\n"
            f"Phone: {session.get('user.phone', 'N/A')}\n\n"
            f"Is this correct? (Yes/No, or add more details)"
        )
        session["awaiting_field"] = "confirmation"
        SESSION_CONTEXT[msg.session_id] = session
        return ChatResponse(
            message=confirmation_message,
            missing_fields=[],
            is_ready=False,
            context=session
        )

    # Step 5. Confirmed → create complaint internally (no HTTP call)
    # Verify intent is still complaint (shouldn't have gotten here otherwise, but double-check)
    intent = session.get("intent", "complaint")
    if intent not in ["complaint", "other"]:
        SESSION_CONTEXT[msg.session_id] = session
        return ChatResponse(
            message=f"I understand this is a {intent}. For complaints, please describe the issue you'd like to file. For other needs, please contact the department directly.",
            is_ready=False,
            context=session
        )
    
    # Match the ComplaintCreate schema from backend
    backend_payload = ComplaintCreate(
        title=(session.get("description") or "Chatbot Complaint")[:60],
        description=session.get("description") or "No description provided",
        transcript=session.get("raw_text"),
        language=session.get("language"),
        translated_text=session.get("translated_text") or session.get("description"),
        category=session.get("category"),
        subcategory=session.get("subcategory"),
        department_code=session.get("department_code") or "PW",
        source="chatbot",
        complaint_metadata={
            "location": session.get("location"),
            "phone": session.get("user.phone"),
            "intent": intent
        }
    )

    try:
        # Call internal function directly instead of HTTP call
        logger.info(f"Creating complaint internally with payload: {backend_payload}")
        complaint_response = ai_create_complaint_internal(backend_payload, db)
        logger.info(f"Complaint created successfully: {complaint_response}")
        
        session["backend_reference"] = complaint_response.reference_no
        message = f"✅ Your complaint has been filed successfully!\n\n📋 Reference No: {session['backend_reference']}\n📁 Department: {session.get('category', 'General')}\n📍 Location: {session.get('location', 'N/A')}\n\nYou can track your complaint status using the reference number. Is there anything else I can help you with?"
        
    except Exception as e:
        logger.error(f"Error creating complaint: {e}")
        session["backend_reference"] = "ERROR"
        message = "There was an error processing your complaint. Please try again later or contact support."

    SESSION_CONTEXT[msg.session_id] = session

    return ChatResponse(
        message=message,
        is_ready=True,
        backend_reference=session["backend_reference"],
        context=session
    )

