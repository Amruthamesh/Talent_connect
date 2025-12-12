"""
Seed script for HR document templates
Run with: python -m app.db.seed_templates
"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.document import DocumentTemplate


TEMPLATE_DATA = [
    {
        "name": "Offer Letter",
        "category": "recruitment",
        "file_path": "templates/Offer_Letter.pdf",
        "description": "Standard employment offer letter for new hires",
        "required_fields": [
            "employee_name",
            "designation",
            "department",
            "joining_date",
            "salary",
            "location"
        ],
        "optional_fields": [
            "employee_code",
            "phone_number",
            "email",
            "reporting_manager",
            "probation_period"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Experience Letter",
        "category": "employment",
        "file_path": "templates/Experience_Letter.pdf",
        "description": "Experience certificate for employees",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "joining_date",
            "last_working_date"
        ],
        "optional_fields": [
            "department",
            "achievements",
            "skills"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Relieving Letter",
        "category": "exit",
        "file_path": "templates/Relieving_Letter.pdf",
        "description": "Formal relieving letter for exiting employees",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "last_working_date"
        ],
        "optional_fields": [
            "department",
            "reason_for_leaving",
            "notice_period_served"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Probation Confirmation Letter",
        "category": "employment",
        "file_path": "templates/Probation_Confirmation_Letter.pdf",
        "description": "Letter confirming permanent employment after probation",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "joining_date",
            "confirmation_date"
        ],
        "optional_fields": [
            "department",
            "probation_feedback"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Bonus Letter",
        "category": "compensation",
        "file_path": "templates/Bonus_Letter.pdf",
        "description": "Letter confirming bonus payment",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "bonus_amount",
            "bonus_type"
        ],
        "optional_fields": [
            "performance_rating",
            "payment_date",
            "remarks"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Termination Letter",
        "category": "exit",
        "file_path": "templates/Termination_Letter.pdf",
        "description": "Formal termination letter",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "termination_date",
            "reason"
        ],
        "optional_fields": [
            "notice_period",
            "last_working_date",
            "final_settlement_details"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    }
]


async def seed_templates():
    """Seed document templates into database"""
    async with AsyncSessionLocal() as session:
        for template_data in TEMPLATE_DATA:
            # Check if template already exists
            result = await session.execute(
                select(DocumentTemplate).where(
                    DocumentTemplate.name == template_data["name"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                template = DocumentTemplate(**template_data)
                session.add(template)
                print(f"✓ Added template: {template_data['name']}")
            else:
                print(f"- Template already exists: {template_data['name']}")
        
        await session.commit()
    
    print(f"\n✅ Seeded {len(TEMPLATE_DATA)} document templates")


if __name__ == "__main__":
    asyncio.run(seed_templates())
