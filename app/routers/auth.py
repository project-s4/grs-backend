from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DatabaseError
from typing import Dict, Any, Optional, cast
from app.db.session import get_db
from app.core.security import (
    verify_password, create_access_token, get_password_hash, decode_access_token
)
from app.schemas.users import UserCreate, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.models.models import User, UserRole
from datetime import datetime, timedelta
import secrets
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        new_user = User(
            id=uuid.uuid4(),
            name=user.name,
            email=user.email,
            phone=user.phone,
            password_hash=hashed_password,
            role=user.role,
            department_id=user.department_id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            phone=new_user.phone,
            email=new_user.email,
            role=new_user.role
        )
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in register: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in register: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during registration. Please try again."
        )

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        # Query user by email using SQLAlchemy
        user = db.query(User).filter(User.email == form_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract values from user object
        user_dict = {
            "sub": str(user.email),
            "id": str(user.id),
            "name": str(user.name),
            "email": str(user.email),
            "role": str(user.role.value) if hasattr(user.role, 'value') else str(user.role),
            "department_id": str(user.department_id) if user.department_id else None
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
    except HTTPException:
        # Re-raise HTTP exceptions (like 401)
        raise
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in login: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during login. Please try again."
        )

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            return {"message": "If an account exists with this email, a password reset link has been sent."}
        
        reset_token = secrets.token_urlsafe(32)
        reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        user.reset_token = reset_token
        user.reset_token_expiry = reset_token_expiry
        db.commit()
        
        # In production, send email with reset link
        # For now, return token in response (remove in production!)
        return {"message": "If an account exists with this email, a password reset link has been sent.", "token": reset_token}
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in forgot_password: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in forgot_password: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again."
        )

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.reset_token == request.token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid reset token")
        
        current_time = datetime.utcnow()
        
        if user.reset_token_expiry is None or user.reset_token_expiry < current_time:
            raise HTTPException(status_code=400, detail="Reset token has expired")
        
        user.password_hash = get_password_hash(request.new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()
        
        return {"message": "Password has been reset successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions (like 400)
        raise
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in reset_password: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in reset_password: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again."
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        email = str(payload.get("sub", ""))
        if not email:
            raise credentials_exception
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise credentials_exception
        
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 401)
        raise
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in get_current_user: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again."
        )
