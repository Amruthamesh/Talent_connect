from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.db.session import get_db
from app.core.auth import verify_password, create_access_token, get_current_active_user
from app.models.user import User
from app.schemas.user import LoginResponse, UserResponse, Token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    Returns JWT token and user information
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_user(user)
    )


@router.post("/demo-login", response_model=LoginResponse)
async def demo_login(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Quick login with demo account (no password required)
    Only works if ENABLE_DEMO_ACCOUNTS is True
    """
    if not settings.ENABLE_DEMO_ACCOUNTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo accounts are disabled"
        )
    
    email = request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo account not found"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_user(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return UserResponse.from_user(current_user)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout (client should discard the token)
    """
    return {"message": "Successfully logged out"}
