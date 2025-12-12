"""
Field validation utilities for document generation
Validates user input based on field type and constraints
"""
import re
from datetime import datetime
from typing import Dict, Any, Tuple


class FieldValidator:
    """Validates document fields based on type and constraints"""
    
    # Field type patterns
    PATTERNS = {
        'name': r'^[A-Za-z\s\.\-\']+$',  # Letters, spaces, dots, hyphens, apostrophes
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[\+]?[0-9\s\-\(\)]{10,15}$',
        'employee_code': r'^[A-Z0-9\-]{3,20}$',
        'designation': r'^[A-Za-z\s\-\/\&]+$',
        'department': r'^[A-Za-z\s\-\/\&]+$',
        'address': r'^[A-Za-z0-9\s\,\.\-\#\/]+$',
        'city': r'^[A-Za-z\s\-]+$',
        'state': r'^[A-Za-z\s\-]+$',
        'pincode': r'^[0-9]{5,6}$',
        'date': r'^.+$',  # Accept any string, validate with datetime parsing
        'salary': r'^[0-9]+(\.[0-9]{1,2})?$',
        'percentage': r'^[0-9]+(\.[0-9]{1,2})?$',
        'text': r'^.+$',  # Any non-empty text
    }
    
    # Field type mapping based on field name
    FIELD_TYPES = {
        'employee_name': 'name',
        'candidate_name': 'name',
        'manager_name': 'name',
        'hr_name': 'name',
        'reporting_manager': 'name',
        'name': 'name',
        
        'email': 'email',
        'employee_email': 'email',
        'contact_email': 'email',
        
        'phone': 'phone',
        'phone_number': 'phone',
        'contact_number': 'phone',
        'mobile': 'phone',
        
        'employee_code': 'employee_code',
        'emp_id': 'employee_code',
        'employee_id': 'employee_code',
        
        'position': 'designation',
        'designation': 'designation',
        'job_title': 'designation',
        
        'department': 'department',
        'dept': 'department',
        
        'address': 'address',
        'employee_address': 'address',
        'company_address': 'address',
        
        'city': 'city',
        'state': 'state',
        'pincode': 'pincode',
        'zip_code': 'pincode',
        
        'date_of_joining': 'date',
        'joining_date': 'date',
        'start_date': 'date',
        'end_date': 'date',
        'last_working_day': 'date',
        'effective_date': 'date',
        'offer_acceptance_date': 'date',
        'probation_end_date': 'date',
        
        'salary': 'salary',
        'ctc': 'salary',
        'annual_salary': 'salary',
        'basic_salary': 'salary',
        'bonus_amount': 'salary',
        
        'performance_rating': 'percentage',
        'increment_percentage': 'percentage',
    }
    
    @classmethod
    def validate_field(cls, field_name: str, value: str) -> Tuple[bool, str]:
        """
        Validate a field value
        Returns (is_valid, error_message)
        """
        if not value or not value.strip():
            return False, "This field cannot be empty"
        
        value = value.strip()
        
        # Get field type
        field_type = cls.FIELD_TYPES.get(field_name.lower(), 'text')
        pattern = cls.PATTERNS.get(field_type, cls.PATTERNS['text'])
        
        # Validate against pattern
        if not re.match(pattern, value):
            return False, cls._get_error_message(field_name, field_type, value)
        
        # Additional validations
        if field_type == 'date':
            if not cls._validate_date(value):
                return False, "Invalid date format. Use YYYY-MM-DD, DD/MM/YYYY, or DD-MM-YYYY"
        
        elif field_type == 'salary':
            try:
                amount = float(value)
                if amount <= 0:
                    return False, "Salary must be a positive number"
                if amount > 100000000:  # 10 crore max
                    return False, "Salary amount seems unrealistic"
            except ValueError:
                return False, "Invalid salary amount"
        
        elif field_type == 'percentage':
            try:
                pct = float(value)
                if pct < 0 or pct > 100:
                    return False, "Percentage must be between 0 and 100"
            except ValueError:
                return False, "Invalid percentage"
        
        elif field_type == 'email':
            if len(value) > 100:
                return False, "Email too long"
        
        elif field_type == 'name':
            if len(value) < 2:
                return False, "Name must be at least 2 characters"
            if len(value) > 100:
                return False, "Name too long"
            if any(char.isdigit() for char in value):
                return False, "Name cannot contain numbers"
        
        return True, ""
    
    @classmethod
    def _validate_date(cls, date_str: str) -> bool:
        """Validate date string with flexible natural language parsing"""
        # Common date formats
        formats = [
            '%Y-%m-%d',           # 2024-12-02
            '%d/%m/%Y',           # 02/12/2024
            '%d-%m-%Y',           # 02-12-2024
            '%d %B %Y',           # 2 December 2024
            '%d-%B-%Y',           # 2-December-2024
            '%d %b %Y',           # 2 Dec 2024
            '%d-%b-%Y',           # 2-Dec-2024
            '%B %d, %Y',          # December 2, 2024
            '%b %d, %Y',          # Dec 2, 2024
            '%d/%m/%y',           # 02/12/24
            '%d-%m-%y',           # 02-12-24
            '%m/%d/%Y',           # 12/02/2024 (US format)
            '%Y/%m/%d',           # 2024/12/02
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    @classmethod
    def _get_error_message(cls, field_name: str, field_type: str, value: str) -> str:
        """Get user-friendly error message"""
        messages = {
            'name': f"'{value}' is not a valid name. Please use only letters, spaces, dots, hyphens, and apostrophes.",
            'email': f"'{value}' is not a valid email address. Use format: user@domain.com",
            'phone': f"'{value}' is not a valid phone number. Use 10-15 digits with optional +, spaces, hyphens, or parentheses.",
            'employee_code': f"'{value}' is not a valid employee code. Use 3-20 characters with uppercase letters, numbers, and hyphens.",
            'designation': f"'{value}' is not a valid designation. Use only letters, spaces, hyphens, slashes, and ampersands.",
            'department': f"'{value}' is not a valid department name. Use only letters, spaces, hyphens, slashes, and ampersands.",
            'address': f"'{value}' is not a valid address. Use alphanumeric characters with common punctuation.",
            'city': f"'{value}' is not a valid city name. Use only letters, spaces, and hyphens.",
            'state': f"'{value}' is not a valid state name. Use only letters, spaces, and hyphens.",
            'pincode': f"'{value}' is not a valid PIN code. Use 5-6 digits.",
            'date': f"'{value}' is not a valid date. Try formats like: 2-December-2025, 02/12/2024, 2024-12-02, Dec 2 2024",
            'salary': f"'{value}' is not a valid salary amount. Use numeric values only.",
            'percentage': f"'{value}' is not a valid percentage. Use numeric values between 0 and 100.",
        }
        return messages.get(field_type, f"'{value}' is not valid for {field_name}")
    
    @classmethod
    def get_field_hint(cls, field_name: str) -> str:
        """Get input hint/example for field"""
        field_type = cls.FIELD_TYPES.get(field_name.lower(), 'text')
        
        # Field-specific examples
        field_examples = {
            'employee_name': "Example: John Michael Doe",
            'candidate_name': "Example: Sarah Jane Smith",
            'signatory_name': "Example: Robert Williams",
            'reporting_manager': "Example: Jennifer Anderson",
            
            'designation': "Example: Senior Software Engineer",
            'current_designation': "Example: Software Engineer",
            'new_designation': "Example: Senior Software Engineer",
            
            'company_name': "Example: DHL Supply Chain India Pvt Ltd",
            'company_address': "Example: 123 Tech Park, Whitefield, Bangalore 560066",
            'contact_info': "Example: +91-80-12345678 | hr@company.com",
            
            'salary': "Example: 1200000 (for ₹12 LPA) or 85000 (for $85k)",
            'ctc': "Example: 1500000 (annual package in rupees)",
            'new_salary': "Example: 1500000",
            'bonus_amount': "Example: 50000",
            
            'joining_date': "Example: 1-December-2024, 01/12/2024, or 2024-12-01",
            'date_of_joining': "Example: 15-January-2025 or 15/01/2025",
            'offer_acceptance_date': "Example: 30-November-2024 or 30/11/2024",
            'last_working_date': "Example: 31-December-2024 or 31/12/2024",
            'confirmation_date': "Example: 1-June-2025 or 01/06/2025",
            'effective_date': "Example: 15-Jan-2025 or 15/01/2025",
            
            'email': "Example: john.doe@company.com",
            'phone_number': "Example: +91-9876543210 or 9876543210",
            'employee_code': "Example: EMP2024001 or DHL-001",
            
            'department': "Example: Information Technology",
            'new_department': "Example: Engineering & Development",
            
            'signatory_designation': "Example: Vice President - Human Resources",
            # Locations
            'current_location': "Example: Chennai (city) or Bengaluru, Karnataka",
            'new_location': "Example: Hyderabad (city) or Pune, Maharashtra",
            'location': "Example: Mumbai",
            # Company logo / uploads
            'company_logo': "Upload a PNG/JPG logo image (max 2MB).",
            'signatory_signature': "Upload a PNG/JPG signature image. If it includes name & designation, those fields will be auto-skipped.",
        }
        
        # Return field-specific example if available
        if field_name.lower() in field_examples:
            return field_examples[field_name.lower()]
        
        # Fall back to type-based hints
        type_hints = {
            'name': "Example: John Michael Doe (full name)",
            'email': "Example: your.name@company.com",
            'phone': "Example: +91-9876543210 or (555) 123-4567",
            'employee_code': "Example: EMP2024001 or DHL-EMP-001",
            'designation': "Example: Senior Software Engineer or Manager - Sales",
            'department': "Example: Information Technology or Sales & Marketing",
            'address': "Example: 123 Main Street, Tower A, 5th Floor, City 560001",
            'city': "Example: Bangalore or New York",
            'state': "Example: Karnataka or New York",
            'pincode': "Example: 560001 or 10001",
            'date': "Example: 25-November-2024, 25/11/2024, Nov 25 2024, or 2024-11-25",
            'salary': "Example: 1200000 (₹12 LPA) or 85000 ($85k annual)",
            'percentage': "Example: 15 or 15.5 (for 15% or 15.5%)",
            'text': "Enter any text value"
        }
        return type_hints.get(field_type, "Enter value")
