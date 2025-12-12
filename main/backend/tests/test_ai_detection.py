"""
Unit tests for AI-generated resume detection.
"""

import pytest
from app.utils.ai_detection import AIResumeDetector, check_resume_for_ai


class TestAIResumeDetector:
    """Test AI resume detection functionality."""
    
    def test_human_written_resume(self):
        """Test detection on a clearly human-written resume."""
        human_resume = """
        John Doe
        john@example.com | (555) 123-4567
        
        OBJECTIVE
        Seeking a Software Engineer position where I can apply my 5 years of experience
        in building web applications.
        
        EXPERIENCE
        ABC Corp, New York, NY | 2020 - Present
        Senior Software Engineer
        - Led a team of 4 developers on the payment processing system
        - Fixed critical bugs in the authentication module
        - Wrote unit tests that improved code coverage by 15%
        
        XYZ Company, Boston, MA | 2018 - 2020
        Junior Software Engineer
        - Developed REST APIs using Python and FastAPI
        - Worked on database optimization
        - Collaborated with designers on UI improvements
        
        EDUCATION
        BS in Computer Science, State University | 2018
        """
        
        result = check_resume_for_ai(human_resume)
        
        assert result["confidence_score"] < 50
        assert result["risk_level"] in ["low", "medium"]
        assert not result["is_ai_generated"]
    
    def test_ai_generated_resume_with_common_phrases(self):
        """Test detection on resume with common AI phrases."""
        ai_resume = """
        Jane Smith
        jane.smith@example.com | (555) 987-6543 | LinkedIn.com/in/janesmith
        
        PROFESSIONAL SUMMARY
        Results-driven professional with a proven track record of spearheading 
        innovative solutions and driving growth in dynamic environments. Demonstrated 
        expertise in leveraging best practices to enhance workflow efficiency and 
        deliver exceptional value.
        
        CORE COMPETENCIES
        Strategic Planning, Cross-functional Collaboration, Stakeholder Management,
        Process Optimization, Transformational Leadership
        
        PROFESSIONAL EXPERIENCE
        
        Senior Strategy Manager | Global Tech Solutions | Jan 2020 - Present
        - Spearheaded transformational initiatives resulting in 40% efficiency increase
        - Implemented cutting-edge solutions to optimize operations across departments
        - Leveraged cross-functional collaboration to drive growth and innovation
        - Demonstrated outstanding ability to manage complex stakeholder relationships
        - Achieved unprecedented levels of customer satisfaction through best practices
        
        Strategy Analyst | Leading Enterprises Inc | Jun 2018 - Dec 2019
        - Drove strategic initiatives that enhanced productivity by 35%
        - Collaborated with diverse teams to implement innovative frameworks
        - Optimized business processes utilizing industry-leading methodologies
        
        EDUCATION
        Master of Business Administration | Top Tier University | 2018
        Bachelor of Science in Business Administration | Excellent University | 2016
        """
        
        result = check_resume_for_ai(ai_resume)
        
        # Should detect moderate to high AI likelihood due to phrases
        assert result["confidence_score"] > 45
        assert result["risk_level"] in ["medium", "high"]
        assert len(result["indicators"]) > 0
    
    def test_suspicious_perfection_detection(self):
        """Test detection of suspiciously perfect writing."""
        perfect_resume = """
        Michael Johnson
        michael.johnson@email.com | (555) 234-5678
        
        PROFESSIONAL SUMMARY
        Accomplished professional with a strong background in software development. 
        Skilled in various programming languages and frameworks.
        
        PROFESSIONAL EXPERIENCE
        
        Senior Developer | Tech Company | 2020 - Present
        - Managed development of critical systems
        - Implemented new features successfully
        - Improved system performance significantly
        
        Software Engineer | Another Company | 2018 - 2020
        - Developed software solutions
        - Collaborated with team members
        - Delivered projects on time
        
        SKILLS
        Python, Java, JavaScript, SQL, AWS, Docker, Kubernetes
        
        EDUCATION
        Bachelor of Science in Computer Science | State University | 2018
        """
        
        result = check_resume_for_ai(perfect_resume)
        
        # Should have some suspicion but lower than obvious AI
        assert result["confidence_score"] < 70
    
    def test_empty_resume(self):
        """Test handling of empty or minimal resumes."""
        result = check_resume_for_ai("")
        
        assert result["confidence_score"] == 0
        assert result["risk_level"] == "low"
        assert not result["is_ai_generated"]
    
    def test_short_resume(self):
        """Test handling of very short resumes."""
        short = "John Doe john@example.com"
        result = check_resume_for_ai(short)
        
        assert result["confidence_score"] == 0
        assert result["risk_level"] == "low"
    
    def test_specific_ai_patterns(self):
        """Test detection of specific AI patterns."""
        ai_pattern_resume = """
        EXPERIENCE
        
        Project Manager | Company A | 2020 - Present
        - Sought to enhance workflow efficiency through systematic approach
        - Implemented comprehensive solution to improve process effectiveness
        - Collaborated with team to drive improvement in key metrics
        - Achieved 50% increase in productivity through targeted initiatives
        - Optimized workflow to streamline operations and maximize efficiency
        - Leveraged best practices to deliver exceptional results
        - Drove strategic growth through innovative transformation
        - Spearheaded initiatives resulting in 45% improvement
        - Implemented cutting-edge solutions across departments
        """
        
        result = check_resume_for_ai(ai_pattern_resume)
        
        # Should detect some AI patterns
        assert result["confidence_score"] > 20
        assert result["detailed_analysis"]["ai_patterns_score"] > 0
    
    def test_metadata_analysis(self):
        """Test metadata-based detection."""
        normal_resume = """
        John Smith
        john@example.com
        
        EXPERIENCE
        Software Engineer at Tech Company | 2020-Present
        - Developed web applications
        - Worked on backend systems
        - Collaborated with team members
        
        EDUCATION
        BS Computer Science
        """
        
        metadata = {
            "producer": "ChatGPT Generator",
            "created_date": "2024-01-15",
            "content_type": "application/pdf"
        }
        
        result = check_resume_for_ai(normal_resume, metadata)
        
        # Metadata analysis should be included in detailed analysis
        assert "detailed_analysis" in result
        assert "metadata_score" in result["detailed_analysis"]
    
    def test_confidence_score_range(self):
        """Test that confidence scores are within valid range."""
        test_resumes = [
            "",
            "Short resume",
            "This is a human written resume with some details about my work experience.",
            """
            Results-driven professional with proven track record of spearheading 
            innovative solutions and driving growth through strategic initiatives 
            and leveraging best practices.
            """,
        ]
        
        for resume in test_resumes:
            result = check_resume_for_ai(resume)
            assert 0 <= result["confidence_score"] <= 100
            assert result["risk_level"] in ["high", "medium", "low"]
            assert isinstance(result["is_ai_generated"], bool)
    
    def test_detailed_analysis_structure(self):
        """Test that detailed analysis has all required fields."""
        resume = """
        This is a sample resume with various content.
        Professional experience includes software development.
        Skills: Python, Java, JavaScript
        """
        
        result = check_resume_for_ai(resume)
        
        assert "detailed_analysis" in result
        assert "common_phrases_score" in result["detailed_analysis"]
        assert "ai_patterns_score" in result["detailed_analysis"]
        assert "perfection_score" in result["detailed_analysis"]
        assert "language_metrics_score" in result["detailed_analysis"]
        assert "structure_score" in result["detailed_analysis"]
        assert "metadata_score" in result["detailed_analysis"]
    
    def test_indicators_present_when_high_score(self):
        """Test that indicators are provided when AI is detected."""
        ai_resume = """
        Results-driven professional demonstrating proven track record. 
        Spearheaded innovative solutions with transformational impact.
        Leveraged best practices across cross-functional teams.
        Achieved unprecedented growth through strategic initiatives.
        Core competencies include stakeholder management and synergy.
        Implemented cutting-edge solutions for dynamic environments.
        """
        
        result = check_resume_for_ai(ai_resume)
        
        if result["confidence_score"] > 50:
            assert len(result["indicators"]) > 0
            for indicator in result["indicators"]:
                assert "type" in indicator
                assert "score" in indicator
                assert "message" in indicator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
