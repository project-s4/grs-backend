from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from supabase import Client
from typing import Dict, Any, Optional, cast
from app.db.session import get_db
from app.core.security import (
    verify_password, create_access_token, get_password_hash, decode_access_token
)
from app.schemas.users import UserCreate, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.models.models import UserRole
from datetime import datetime, timedelta
import secrets
import uuid

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Client = Depends(get_db)):
    # Check if email exists
    response = db.from_('users').select('*').eq('email', user.email).execute()
    if response.data and len(response.data) > 0:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user_data = {
        'id': str(uuid.uuid4()),
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'password_hash': hashed_password,
        'role': user.role.value if hasattr(user.role, 'value') else str(user.role),
        'department_id': str(user.department_id) if user.department_id else None,
        'created_at': datetime.utcnow().isoformat()
    }
    
    response = db.from_('users').insert(new_user_data).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=500, detail="Failed to create user")
        
    created_user_data = cast(Dict[str, Any], response.data[0])
    return UserResponse(
        id=uuid.UUID(str(created_user_data['id'])),
        name=str(created_user_data['name']),
        phone=str(created_user_data['phone']),
        email=str(created_user_data['email']),
        role=user.role
    )

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Client = Depends(get_db)):
    # Query Supabase for user by email
    response = db.from_('users').select('*').eq('email', form_data.username).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = cast(Dict[str, Any], response.data[0])
    
    if not verify_password(form_data.password, str(user_data['password_hash'])):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract values from user dict
    user_dict = {
        "sub": str(user_data['email']),
        "id": str(user_data['id']),
        "name": str(user_data['name']),
        "email": str(user_data['email']),
        "role": str(user_data['role']),
        "department_id": str(user_data['department_id']) if user_data.get('department_id') else None
    }
    
    access_token = create_access_token(data=user_dict)
    
    # Return response
    return {
        "access_token": access_token,
        "token": access_token,  # For frontend compatibility
        "token_type": "bearer",
        "user": {
            "id": user_dict["id"],
            "email": user_dict["email"],
            "name": user_dict["name"],
            "role": user_dict["role"],
            "department_id": user_dict["department_id"]
        }
    }

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Client = Depends(get_db)):
    response = db.from_('users').select('*').eq('email', request.email).execute()
    if not response.data or len(response.data) == 0:
        return {"message": "If an account exists with this email, a password reset link has been sent."}
    
    user_data = cast(Dict[str, Any], response.data[0])
    reset_token = secrets.token_urlsafe(32)
    reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    
    response = db.from_('users').update({
        'reset_token': reset_token,
        'reset_token_expiry': reset_token_expiry.isoformat()
    }).eq('id', user_data['id']).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update reset token")
    
    # In production, send email with reset link
    # For now, return token in response (remove in production!)
    return {"message": "If an account exists with this email, a password reset link has been sent.", "token": reset_token}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Client = Depends(get_db)):
    response = db.from_('users').select('*').eq('reset_token', request.token).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    user_data = cast(Dict[str, Any], response.data[0])
    current_time = datetime.utcnow()
    
    try:
        expiry_time = datetime.fromisoformat(str(user_data['reset_token_expiry']))
    except (ValueError, TypeError, KeyError):
        expiry_time = None
    
    if expiry_time is None or expiry_time < current_time:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    response = db.from_('users').update({
        'password_hash': get_password_hash(request.new_password),
        'reset_token': None,
        'reset_token_expiry': None
    }).eq('id', user_data['id']).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return {"message": "Password has been reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Client = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email = str(payload.get("sub", ""))
    if email is None:
        raise credentials_exception
    
    response = db.from_('users').select('*').eq('email', email).execute()
    if not response.data or len(response.data) == 0:
        raise credentials_exception
    
    user_data = cast(Dict[str, Any], response.data[0])
    return UserResponse(
        id=uuid.UUID(str(user_data['id'])),
        name=str(user_data['name']),
        email=str(user_data['email']),
        phone=str(user_data['phone']),
        role=UserRole(user_data['role'])
    )
