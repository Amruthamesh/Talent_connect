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
        "file_path": "templates/offer_letter.docx",
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
        "file_path": "templates/experience_letter.docx",
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
        "file_path": "templates/relieving_letter.docx",
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
        "name": "Appointment Letter",
        "category": "recruitment",
        "file_path": "templates/appointment_letter.docx",
        "description": "Official appointment letter with detailed terms",
        "required_fields": [
            "employee_name",
            "designation",
            "department",
            "joining_date",
            "salary",
            "location",
            "employee_code"
        ],
        "optional_fields": [
            "phone_number",
            "email",
            "reporting_manager",
            "probation_period",
            "notice_period",
            "benefits"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Promotion Letter",
        "category": "employment",
        "file_path": "templates/promotion_letter.docx",
        "description": "Letter confirming employee promotion",
        "required_fields": [
            "employee_name",
            "employee_code",
            "current_designation",
            "new_designation",
            "effective_date",
            "new_salary"
        ],
        "optional_fields": [
            "department",
            "new_department",
            "responsibilities"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Salary Increment Letter",
        "category": "employment",
        "file_path": "templates/increment_letter.docx",
        "description": "Letter confirming salary revision",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "current_salary",
            "new_salary",
            "effective_date"
        ],
        "optional_fields": [
            "increment_percentage",
            "performance_rating"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Confirmation Letter",
        "category": "employment",
        "file_path": "templates/confirmation_letter.docx",
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
        "name": "Transfer Letter",
        "category": "employment",
        "file_path": "templates/transfer_letter.docx",
        "description": "Letter confirming internal transfer",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "current_location",
            "new_location",
            "effective_date"
        ],
        "optional_fields": [
            "current_department",
            "new_department",
            "reason"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Warning Letter",
        "category": "disciplinary",
        "file_path": "templates/warning_letter.docx",
        "description": "Formal warning letter",
        "required_fields": [
            "employee_name",
            "employee_code",
            "designation",
            "issue_description",
            "warning_level"
        ],
        "optional_fields": [
            "incident_date",
            "corrective_action",
            "consequence"
        ],
        "uses_company_logo": True,
        "uses_company_letterhead": True
    },
    {
        "name": "Internship Offer Letter",
        "category": "recruitment",
        "file_path": "templates/internship_offer.docx",
        "description": "Offer letter for interns",
        "required_fields": [
            "candidate_name",
            "internship_role",
            "start_date",
            "duration",
            "stipend"
        ],
        "optional_fields": [
            "phone_number",
            "email",
            "department",
            "reporting_manager",
            "project_description"
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
