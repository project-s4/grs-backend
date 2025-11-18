from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DatabaseError
from pydantic import BaseModel
from app.db.session import get_db
from app.core.security import get_current_user
from app.db.supabase import verify_supabase_token
from app.schemas.users import UserProfileCreate, UserResponse
from app.models.models import User, UserRole
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TokenRequest(BaseModel):
    token: str

@router.post("/verify")
async def verify_token(request: TokenRequest, db: Session = Depends(get_db)):
    """Verify Supabase token and return user profile."""
    try:
        # Verify token with Supabase
        supabase_user = verify_supabase_token(request.token)
        if supabase_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Find user in local database
        user = db.query(User).filter(User.supabase_user_id == supabase_user["id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete registration."
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

@router.post("/create-profile", response_model=UserResponse)
async def create_profile(profile: UserProfileCreate, db: Session = Depends(get_db)):
    """Create user profile in local database after Supabase signup."""
    try:
        # Note: supabase_user_id is the UUID from Supabase Auth, not a token
        # The frontend has already verified the user via OAuth, so we trust it
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.supabase_user_id == uuid.UUID(profile.supabase_user_id)) |
            (User.email == profile.email)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User profile already exists")
        
        # Create new user profile
        new_user = User(
            id=uuid.uuid4(),
            name=profile.name,
            email=profile.email,
            phone=profile.phone,
            role=profile.role,
            department_id=profile.department_id,
            supabase_user_id=uuid.UUID(profile.supabase_user_id)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            phone=new_user.phone,
            email=new_user.email,
            role=new_user.role,
            supabase_user_id=new_user.supabase_user_id
        )
    except HTTPException:
        raise
    except (OperationalError, DatabaseError) as e:
        logger.error(f"Database error in create_profile: {e}")
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Database connection error. Please check backend configuration."
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_profile: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An error occurred during profile creation. Please try again."
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
