from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DatabaseError
from pydantic import BaseModel
from app.db.session import get_db
from app.core.security import get_current_user, create_access_token
from app.schemas.users import UserResponse
from app.models.models import User, UserRole
import uuid
import logging
import secrets

logger = logging.getLogger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenRequest(BaseModel):
    token: str

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Simple mock login - accepts any username/password."""
    try:
        # Mock authentication - accept any credentials
        # Find or create user by username/email
        user = db.query(User).filter(User.email == request.username).first()
        
        if not user:
            # Create a mock user with default role
            user = User(
                id=uuid.uuid4(),
                name=request.username,
                email=request.username,
                phone="",
                role=UserRole.citizen,
                supabase_user_id=uuid.uuid4()  # Generate a random UUID for mock auth
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate a simple token
        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                role=user.role,
                supabase_user_id=user.supabase_user_id
            )
        }
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in login: {e}")
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again."
        )

@router.post("/verify")
async def verify_token(request: TokenRequest, db: Session = Depends(get_db)):
    """Verify token and return user profile."""
    try:
        from app.core.security import decode_access_token
        
        # Decode token
        payload = decode_access_token(request.token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Find user in database
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role,
            supabase_user_id=user.supabase_user_id
        )
    except HTTPException:
        raise
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in verify: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in verify: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again."
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        supabase_user_id=current_user.supabase_user_id
    )
