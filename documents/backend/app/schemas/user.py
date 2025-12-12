from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str
    role: str


class UserCreate(UserBase):
    """Schema for creating user"""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """User schema with database fields"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Public user response"""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    label: str  # Matches frontend demo account structure
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_user(cls, user):
        """Create response from User model"""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            label=user.full_name
        )


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT token payload"""
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    username: EmailStr  # Using 'username' to match OAuth2 standard
    password: str


class LoginResponse(BaseModel):
    """Login response with user data"""
    access_token: str
    token_type: str
    user: UserResponse
