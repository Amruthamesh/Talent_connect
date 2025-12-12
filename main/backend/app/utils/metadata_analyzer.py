"""
Metadata analysis and filtering utilities for candidate profiling.
Helps analyze extracted metadata to improve candidate ranking and matching.
"""
from typing import Dict, List, Any, Tuple
from app.utils.metadata_extractor import MetadataExtractor


class MetadataAnalyzer:
    """Analyze and score document metadata for recruitment purposes."""
    
    @staticmethod
    def calculate_document_quality_score(metadata: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculate a quality score for the document (0-100).
        
        Args:
            metadata: Document metadata dictionary
            
        Returns:
            Tuple of (score, quality_level) where quality_level is "high", "medium", or "low"
        """
        score = 100.0
        reasons = []
        
        # Penalize if document is scanned (non-selectable text)
        if metadata.get("is_scanned", False):
            score -= 20
            reasons.append("Document appears to be scanned")
        
        # Bonus for large text content (likely detailed resume)
        text_length = metadata.get("text_length", 0)
        if text_length > 5000:
            score += 10
            reasons.append("Comprehensive document")
        elif text_length < 1000:
            score -= 15
            reasons.append("Minimal content")
        
        # Score based on entity extraction
        entities = metadata.get("entities", {})
        email_count = len(entities.get("emails", []))
        phone_count = len(entities.get("phones", []))
        
        if email_count > 0:
            score += 5
        if phone_count > 0:
            score += 5
        
        # Score based on sections detected
        sections = metadata.get("sections", {})
        section_count = len(sections)
        
        if section_count >= 4:
            score += 10
            reasons.append("Well-structured document")
        elif section_count < 2:
            score -= 10
            reasons.append("Poorly structured")
        
        # Score based on skills found
        skills_found = len(entities.get("skills", []))
        if skills_found >= 5:
            score += 10
            reasons.append("Rich skill information")
        elif skills_found == 0:
            score -= 10
            reasons.append("No skills detected")
        
        # Cap score between 0 and 100
        score = max(0, min(100, score))
        
        # Determine quality level
        if score >= 75:
            quality_level = "high"
        elif score >= 50:
            quality_level = "medium"
        else:
            quality_level = "low"
        
        return score, quality_level
    
    @staticmethod
    def filter_candidates_by_metadata(
        candidates: List[Dict[str, Any]], 
        min_quality_score: float = 50.0
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter candidates based on document metadata quality.
        
        Args:
            candidates: List of candidate profiles with metadata
            min_quality_score: Minimum acceptable quality score (0-100)
            
        Returns:
            Tuple of (qualified_candidates, disqualified_candidates)
        """
        qualified = []
        disqualified = []
        
        for candidate in candidates:
            metadata = candidate.get("metadata", {})
            score, quality_level = MetadataAnalyzer.calculate_document_quality_score(metadata)
            
            candidate_copy = candidate.copy()
            candidate_copy["document_quality_score"] = score
            candidate_copy["document_quality_level"] = quality_level
            
            if score >= min_quality_score:
                qualified.append(candidate_copy)
            else:
                disqualified.append(candidate_copy)
        
        return qualified, disqualified
    
    @staticmethod
    def extract_key_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metadata fields for display and analysis.
        
        Args:
            metadata: Full metadata dictionary
            
        Returns:
            Dictionary with key metadata fields
        """
        entities = metadata.get("entities", {})
        sections = metadata.get("sections", {})
        
        return {
            "document_type": metadata.get("content_type", "unknown"),
            "is_scanned": metadata.get("is_scanned", False),
            "page_count": metadata.get("page_count"),
            "has_selectable_text": metadata.get("has_selectable_text", True),
            "detected_sections": list(sections.keys()),
            "contact_info": {
                "emails": entities.get("emails", []),
                "phones": entities.get("phones", []),
                "locations": entities.get("locations", []),
            },
            "professional_info": {
                "skills": entities.get("skills", []),
                "degrees": entities.get("degrees", []),
                "dates": entities.get("dates", []),
            },
            "extraction_confidence": {
                "has_emails": len(entities.get("emails", [])) > 0,
                "has_phones": len(entities.get("phones", [])) > 0,
                "has_skills": len(entities.get("skills", [])) > 0,
                "has_sections": len(sections) > 0,
            }
        }
    
    @staticmethod
    def rank_candidates_by_metadata(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank candidates based on document metadata quality and completeness.
        
        Args:
            candidates: List of candidate profiles with metadata
            
        Returns:
            Sorted list with metadata ranking scores
        """
        candidates_with_scores = []
        
        for candidate in candidates:
            metadata = candidate.get("metadata", {})
            score, quality_level = MetadataAnalyzer.calculate_document_quality_score(metadata)
            
            candidate_copy = candidate.copy()
            candidate_copy["metadata_quality_score"] = score
            candidate_copy["metadata_quality_level"] = quality_level
            
            candidates_with_scores.append(candidate_copy)
        
        # Sort by metadata quality score (descending)
        return sorted(
            candidates_with_scores,
            key=lambda c: c.get("metadata_quality_score", 0),
            reverse=True
        )
    
    @staticmethod
    def get_metadata_summary(metadata: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of document metadata.
        
        Args:
            metadata: Document metadata dictionary
            
        Returns:
            Formatted summary string
        """
        entities = metadata.get("entities", {})
        sections = metadata.get("sections", {})
        
        summary_parts = []
        
        # Document type
        content_type = metadata.get("content_type", "unknown")
        is_scanned = metadata.get("is_scanned", False)
        doc_type = f"{content_type} ({'scanned' if is_scanned else 'native'})"
        summary_parts.append(f"Document Type: {doc_type}")
        
        # Content quality
        text_length = metadata.get("text_length", 0)
        summary_parts.append(f"Content Length: {text_length} characters")
        
        # Detected sections
        if sections:
            section_list = ", ".join(sections.keys())
            summary_parts.append(f"Detected Sections: {section_list}")
        
        # Key entities
        emails = entities.get("emails", [])
        phones = entities.get("phones", [])
        skills = entities.get("skills", [])
        
        if emails:
            summary_parts.append(f"Emails Found: {', '.join(emails)}")
        if phones:
            summary_parts.append(f"Phones Found: {', '.join(phones)}")
        if skills:
            skill_preview = ", ".join(skills[:5])
            if len(skills) > 5:
                skill_preview += f", +{len(skills)-5} more"
            summary_parts.append(f"Skills Detected: {skill_preview}")
        
        return "\n".join(summary_parts)
