"""
Seed script for demo users
Run with: python -m app.db.seed_users
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.db.base import Base
from app.models.user import User
from app.core.auth import get_password_hash


# Demo users data
DEMO_USERS = [
    {
        "email": "hr@dhl.com",
        "password": "password123",
        "full_name": "HR Manager",
        "role": "hr",
        "is_active": True
    },
    {
        "email": "admin@dhl.com",
        "password": "password123",
        "full_name": "Administrator",
        "role": "admin",
        "is_active": True
    },
    {
        "email": "recruiter@dhl.com",
        "password": "password123",
        "full_name": "Recruiter",
        "role": "recruiter",
        "is_active": True
    },
    {
        "email": "candidate@dhl.com",
        "password": "password123",
        "full_name": "Candidate",
        "role": "candidate",
        "is_active": True
    }
]


async def seed_users():
    """Seed demo users into database"""
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        try:
            for user_data in DEMO_USERS:
                # Check if user already exists
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"⏭️  Skipping {user_data['email']} (already exists)")
                    continue
                
                # Create new user
                user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=user_data["is_active"]
                )
                
                session.add(user)
                print(f"✅ Created user: {user_data['email']} (role: {user_data['role']})")
            
            await session.commit()
            print(f"\n✅ Successfully seeded {len(DEMO_USERS)} demo users")
            print("\nAvailable demo accounts:")
            for user_data in DEMO_USERS:
                print(f"  - Email: {user_data['email']}, Password: {user_data['password']}, Role: {user_data['role']}")
        
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding users: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_users())
