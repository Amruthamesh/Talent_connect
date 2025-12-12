from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base  # ensures models are imported
from app.models import User
from app.models.document import DocumentTemplate
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
    
    # Initialize HR Letter Templates
    await init_document_templates(session)
    
    print("✅ Database initialized with demo accounts and templates")


async def init_document_templates(session: AsyncSession):
    """Initialize Corporate HR Letter Templates"""
    
    templates = [
        {
            "name": "Offer Letter - Full Time",
            "category": "recruitment", 
            "description": "Standard corporate offer letter for full-time employees",
            "required_fields": [
                "candidate_name", "position", "department", "start_date", 
                "salary", "reporting_manager", "hr_contact"
            ],
            "optional_fields": [
                "middle_name", "employee_id", "probation_period", "benefits", 
                "work_location", "notice_period"
            ]
        },
        {
            "name": "Offer Letter - Internship", 
            "category": "recruitment",
            "description": "Corporate internship offer letter template",
            "required_fields": [
                "candidate_name", "internship_position", "department", "start_date", 
                "end_date", "stipend", "supervisor", "hr_contact"
            ],
            "optional_fields": [
                "middle_name", "university", "course", "semester", "work_location"
            ]
        },
        {
            "name": "Experience Letter",
            "category": "employment",
            "description": "Corporate experience certificate for employees",
            "required_fields": [
                "employee_name", "employee_id", "designation", "department", 
                "joining_date", "last_working_date", "hr_signatory"
            ],
            "optional_fields": [
                "middle_name", "salary", "performance_rating", "achievements"
            ]
        },
        {
            "name": "Promotion Letter", 
            "category": "employment",
            "description": "Corporate promotion announcement letter",
            "required_fields": [
                "employee_name", "current_position", "new_position", "department", 
                "effective_date", "new_salary", "reporting_manager"
            ],
            "optional_fields": [
                "employee_id", "previous_salary", "congratulations_note"
            ]
        },
        {
            "name": "Transfer Letter",
            "category": "employment", 
            "description": "Corporate employee transfer letter",
            "required_fields": [
                "employee_name", "employee_id", "current_department", "new_department",
                "current_location", "new_location", "transfer_date", "new_manager"
            ],
            "optional_fields": [
                "reason", "salary_change", "relocation_allowance"
            ]
        },
        {
            "name": "Resignation Acceptance",
            "category": "exit",
            "description": "Corporate resignation acceptance letter", 
            "required_fields": [
                "employee_name", "employee_id", "position", "department",
                "resignation_date", "last_working_date", "notice_period", "hr_contact"
            ],
            "optional_fields": [
                "reason", "exit_formalities", "final_settlement_date"
            ]
        },
        {
            "name": "Relieving Letter",
            "category": "exit",
            "description": "Corporate relieving letter for exiting employees",
            "required_fields": [
                "employee_name", "employee_id", "designation", "department",
                "joining_date", "relieving_date", "hr_signatory"
            ],
            "optional_fields": [
                "performance_summary", "dues_clearance", "return_assets"
            ]
        },
        {
            "name": "Warning Letter",
            "category": "disciplinary", 
            "description": "Corporate disciplinary warning letter",
            "required_fields": [
                "employee_name", "employee_id", "department", "incident_date",
                "violation_details", "warning_level", "manager_name"
            ],
            "optional_fields": [
                "previous_warnings", "improvement_plan", "review_date"
            ]
        },
        {
            "name": "Appreciation Letter",
            "category": "recognition",
            "description": "Corporate employee appreciation letter", 
            "required_fields": [
                "employee_name", "department", "achievement", "recognition_date",
                "manager_name"
            ],
            "optional_fields": [
                "employee_id", "project_name", "reward_amount", "team_members"
            ]
        },
        {
            "name": "Salary Increment Letter",
            "category": "employment",
            "description": "Corporate salary increment notification",
            "required_fields": [
                "employee_name", "employee_id", "current_salary", "new_salary", 
                "increment_percentage", "effective_date", "hr_approval"
            ],
            "optional_fields": [
                "performance_rating", "market_adjustment", "promotion_linked"
            ]
        }
    ]
    
    from sqlalchemy import select
    for template_data in templates:
        # Check if template already exists
        result = await session.execute(
            select(DocumentTemplate).where(DocumentTemplate.name == template_data["name"])
        )
        existing_template = result.scalar_one_or_none()
        
        if not existing_template:
            template = DocumentTemplate(
                name=template_data["name"],
                category=template_data["category"], 
                description=template_data["description"],
                required_fields=template_data["required_fields"],
                optional_fields=template_data["optional_fields"],
                file_path=f"templates/{template_data['name'].lower().replace(' ', '_')}.docx",
                uses_company_logo=True,
                uses_company_letterhead=True,
                is_active=True
            )
            session.add(template)
    
    await session.commit()
    print("✅ Corporate HR Letter Templates initialized")


if __name__ == "__main__":
    asyncio.run(init_db())
