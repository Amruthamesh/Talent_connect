from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base  # ensures models are imported
from app.models import User
from app.core.auth import get_password_hash
import asyncio


async def init_db():
    """Initialize database with demo accounts"""
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create demo accounts
    demo_accounts = [
        {
            "email": "hr@talent.com",
            "password": "hr123",
            "full_name": "HR Manager Demo",
            "role": "hr",
            "is_active": True
        },
        {
            "email": "manager@talent.com",
            "password": "mgr123",
            "full_name": "Hiring Manager Demo",
            "role": "hiring_manager",
            "is_active": True
        },
        {
            "email": "recruiter@talent.com",
            "password": "rec123",
            "full_name": "Recruiter Demo",
            "role": "recruiter",
            "is_active": True
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for account in demo_accounts:
            # Check if user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.email == account["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                user = User(
                    email=account["email"],
                    hashed_password=get_password_hash(account["password"]),
                    full_name=account["full_name"],
                    role=account["role"],
                    is_active=account["is_active"]
                )
                session.add(user)
        
        await session.commit()
    
    print("✅ Database initialized with demo accounts")


if __name__ == "__main__":
    asyncio.run(init_db())
