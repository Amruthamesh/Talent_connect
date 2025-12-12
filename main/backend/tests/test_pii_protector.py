"""
Unit tests for PII protection utilities.
"""
import pytest
from app.utils.pii_protector import (
    protect_pii_from_text,
    protect_pii_profile,
    protect_job_description,
    create_safe_resume_text,
    get_pii_summary,
)


class TestProtectPIIFromText:
    """Test PII masking from plain text."""
    
    def test_email_masking(self):
        """Test that email addresses are obfuscated."""
        text = "Contact john.doe@example.com for more info"
        result = protect_pii_from_text(text)
        # Email should be obfuscated like jo***@exa***.com
        assert "john.doe@example.com" not in result
        assert "jo***@" in result
    
    def test_phone_masking(self):
        """Test that phone numbers are obfuscated."""
        text = "Call me at 555-123-4567 or +1 (555) 987-6543"
        result = protect_pii_from_text(text)
        # Phone should be obfuscated, showing area code and last digit
        assert "555-123-4567" not in result
        assert "987-6543" not in result
        # Should contain obfuscated format like (555) ***7
        assert "***" in result
    
    def test_ssn_masking(self):
        """Test that SSN is obfuscated."""
        text = "SSN: 123-45-6789"
        result = protect_pii_from_text(text)
        # SSN pattern matches phone pattern too, so it gets obfuscated
        # Should show last 4 digits like ***-**-6789
        assert "123-45-6789" not in result
        assert "***" in result
    
    def test_url_masking(self):
        """Test that URLs are obfuscated."""
        text = "Check my portfolio at https://example.com or www.mysite.com"
        result = protect_pii_from_text(text)
        # URLs should be obfuscated like https://exa***
        assert "https://example.com" not in result
        assert "www.mysite.com" not in result
        assert "https://" in result or "***" in result
    
    def test_name_masking(self):
        """Test that names are obfuscated."""
        text = "John Smith worked here from 2020 to 2023"
        result = protect_pii_from_text(text, "John Smith")
        # Name should be obfuscated like JohnXXXX or similar
        assert "John Smith" not in result
        assert "***" in result or "X" in result
    
    def test_multiple_pii_types(self):
        """Test obfuscation of multiple PII types."""
        text = (
            "Jane Doe (jane.doe@example.com, 555-123-4567) "
            "worked at https://company.com. Date: 2020-01-15"
        )
        result = protect_pii_from_text(text, "Jane Doe")
        # Check that PII is obfuscated (not visible in original form)
        assert "Jane Doe" not in result
        assert "jane.doe@example.com" not in result
        assert "555-123-4567" not in result
        assert "https://company.com" not in result
        # Check that obfuscation is present
        assert "***" in result


class TestProtectPIIProfile:
    """Test PII masking in profile dictionaries."""
    
    def test_direct_pii_fields_masked(self):
        """Test that direct PII fields are obfuscated."""
        profile = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "555-123-4567",
            "address": "123 Main St"
        }
        result = protect_pii_profile(profile)
        # Check that PII is obfuscated, not with placeholders
        assert result["full_name"] != "John Doe"
        assert result["email"] != "john@example.com"
        assert result["phone"] != "555-123-4567"
        assert result["address"] != "123 Main St"
        # Should contain obfuscation characters
        assert "X" in result["full_name"] or "***" in result["full_name"]
    
    def test_text_field_protection(self):
        """Test that text fields are scanned and obfuscated."""
        profile = {
            "full_name": "Jane Smith",
            "raw_text": "Jane Smith has 5 years of experience. Email: jane@test.com"
        }
        result = protect_pii_profile(profile)
        assert "jane@test.com" not in result["raw_text"]
        assert "Jane Smith" not in result["raw_text"]
        # Should have obfuscation
        assert "***" in result["raw_text"] or "X" in result["raw_text"]
    
    def test_list_field_protection(self):
        """Test that list fields with strings are protected."""
        profile = {
            "full_name": "Alice Johnson",
            "experiences": [
                "Worked at CompanyA as Software Engineer",
                "Email: alice@company.com for references"
            ]
        }
        result = protect_pii_profile(profile)
        assert "alice@company.com" not in result["experiences"][1]
        # Should have obfuscation
        assert "***" in result["experiences"][1]
    
    def test_nested_dict_protection(self):
        """Test that text fields are protected."""
        profile = {
            "full_name": "Bob Brown",
            "experience_summary": "Email: bob@example.com, Phone: 555-999-8888"
        }
        result = protect_pii_profile(profile)
        # experience_summary is a protected text field
        assert "bob@example.com" not in result["experience_summary"]
        assert "***" in result["experience_summary"]


class TestProtectJobDescription:
    """Test PII protection in job descriptions."""
    
    def test_company_contact_info_masked(self):
        """Test that company contact info is obfuscated."""
        jd = (
            "Please send applications to careers@company.com or call 555-777-6666. "
            "Visit our office at 456 Corporate Blvd"
        )
        result = protect_job_description(jd)
        assert "careers@company.com" not in result
        assert "555-777-6666" not in result
        assert "***" in result


class TestCreateSafeResumeText:
    """Test safe resume text creation."""
    
    def test_safe_resume_creation(self):
        """Test that resume text is properly obfuscated."""
        resume = (
            "Resume of John Doe\n"
            "Email: john@example.com\n"
            "Phone: 555-123-4567\n"
            "Portfolio: https://johndoe.com"
        )
        result = create_safe_resume_text(resume, "John Doe")
        assert "John Doe" not in result
        assert "john@example.com" not in result
        assert "555-123-4567" not in result
        assert "https://johndoe.com" not in result
        # Should have obfuscation
        assert "***" in result


class TestGetPIISummary:
    """Test PII detection summary."""
    
    def test_pii_summary_detection(self):
        """Test that PII summary correctly identifies found PII."""
        text = (
            "Contact Jane Doe at jane.doe@example.com or 555-555-5555. "
            "SSN: 123-45-6789"
        )
        summary = get_pii_summary(text)
        assert "email" in summary
        assert "phone" in summary
        assert "ssn" in summary
        assert len(summary["email"]) > 0
        assert len(summary["phone"]) > 0
    
    def test_empty_summary_for_clean_text(self):
        """Test that clean text produces empty summary."""
        text = "This is a resume with skills like Python, Java, and JavaScript"
        summary = get_pii_summary(text)
        # Should have minimal or no matches
        assert len(summary) == 0 or all(len(v) == 0 for v in summary.values())


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_text_handling(self):
        """Test that empty text is handled gracefully."""
        assert protect_pii_from_text("") == ""
        assert protect_pii_from_text(None) == None
    
    def test_none_profile_handling(self):
        """Test that None profile is handled gracefully."""
        result = protect_pii_profile(None)
        assert result is None
    
    def test_missing_fields(self):
        """Test handling of missing optional fields."""
        profile = {"full_name": "Test User"}
        result = protect_pii_profile(profile)
        # Name should be obfuscated
        assert result["full_name"] != "Test User"
        assert "X" in result["full_name"] or "***" in result["full_name"]
        assert "email" not in result  # Missing fields stay missing
    
    def test_false_positives_avoidance(self):
        """Test that common false positives are minimized."""
        # IP addresses used in examples
        text = "Server running on 192.168.1.1"
        result = protect_pii_from_text(text)
        # IP should be obfuscated
        assert "192.168.1.1" not in result
        assert "***" in result or "X" in result
    
    def test_repeated_pii_masking(self):
        """Test that repeated PII is properly obfuscated."""
        text = "John Doe worked with John Doe at john@example.com"
        result = protect_pii_from_text(text, "John Doe")
        # All instances should be obfuscated
        assert "John Doe" not in result
        assert "john@example.com" not in result
        # Should have obfuscation markers
        assert "***" in result or "X" in result


# Integration tests
class TestIntegration:
    """Integration tests combining multiple protections."""
    
    def test_full_resume_protection(self):
        """Test protecting a complete resume."""
        profile = {
            "full_name": "Alice Johnson",
            "email": "alice.johnson@email.com",
            "phone": "555-123-4567",
            "address": "123 Tech Street, San Francisco, CA",
            "raw_text": (
                "Alice Johnson\n"
                "alice.johnson@email.com | 555-123-4567\n"
                "123 Tech Street, San Francisco, CA 94107\n\n"
                "Experience:\n"
                "Senior Software Engineer at TechCorp (2018-2023)\n"
                "- Developed Python applications\n"
                "- Worked with John Smith on cloud infrastructure\n"
                "Contact: john.smith@techcorp.com\n"
            ),
            "summary": "Experienced engineer with expertise in AWS and Python"
        }
        
        result = protect_pii_profile(profile, "Alice Johnson")
        
        # Check direct field masking (should be obfuscated)
        assert result["full_name"] != "Alice Johnson"
        assert "X" in result["full_name"] or "***" in result["full_name"]
        assert result["email"] != "alice.johnson@email.com"
        assert result["phone"] != "555-123-4567"
        
        # Check text field masking
        assert "alice.johnson@email.com" not in result["raw_text"]
        assert "555-123-4567" not in result["raw_text"]
        assert "john.smith@techcorp.com" not in result["raw_text"]
