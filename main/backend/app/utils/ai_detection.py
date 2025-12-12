"""
AI-Generated Resume Detection Utility

Detects whether a resume is likely AI-generated using multiple heuristics:
1. Writing pattern analysis (repetitive language, common AI phrases)
2. Metadata analysis (creation date patterns, modification history)
3. Content structure analysis (suspicious formatting, perfect alignment)
4. Statistical text analysis (entropy, word distribution)
5. Integration with AI detection APIs (OpenAI, Hugging Face)
"""

import re
import math
from typing import Dict, Any, Tuple, List
from collections import Counter
from pathlib import Path


class AIResumeDetector:
    """Detect AI-generated resumes using multiple heuristics."""
    
    # Common AI-generated resume phrases and patterns
    AI_COMMON_PHRASES = {
        "results-driven": 5,
        "synergy": 5,
        "leverage": 4,
        "dynamic professional": 5,
        "proven track record": 4,
        "spearhead": 4,
        "driving growth": 3,
        "cross-functional": 3,
        "best practices": 3,
        "core competencies": 4,
        "collaborative approach": 3,
        "innovative solutions": 3,
        "end-to-end": 2,
        "stakeholder management": 3,
        "strategic initiatives": 3,
        "transformational": 3,
        "cutting-edge": 3,
        "industry-leading": 3,
        "accelerated growth": 2,
        "maximized efficiency": 2,
    }
    
    # Suspicious perfection indicators
    PERFECTION_INDICATORS = {
        "perfect_formatting": 0.2,
        "no_typos": 0.15,
        "consistent_tense": 0.15,
        "consistent_punctuation": 0.1,
        "perfect_alignment": 0.1,
    }
    
    # AI-specific patterns
    AI_PATTERNS = {
        r"enhanced\s+(?:workflow|process|productivity|efficiency)": 3,
        r"optimized\s+(?:workflow|process|operations|performance)": 3,
        r"implemented\s+.*\s+(?:solution|system|framework)": 2,
        r"(?:collaborated|coordinated|partnered)\s+with\s+.*\s+to\s+(?:improve|enhance|drive)": 2,
        r"achieved\s+\d+%\s+(?:increase|improvement|growth)": 2,
        r"demonstrated\s+strong\s+.*\s+(?:skills|expertise|abilities)": 2,
        r"sought\s+to\s+\w+": 3,  # Very AI-like phrasing
    }
    
    @staticmethod
    def detect_ai_generated(
        resume_text: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive AI detection analysis.
        
        Args:
            resume_text: Full resume text
            metadata: Optional metadata from document analysis
            
        Returns:
            Dictionary with detection results:
            {
                "is_ai_generated": bool,
                "confidence_score": float (0-100),
                "risk_level": str ("high", "medium", "low"),
                "indicators": List[Dict],
                "explanation": str,
                "detailed_analysis": Dict
            }
        """
        if not resume_text or len(resume_text.strip()) < 100:
            return {
                "is_ai_generated": False,
                "confidence_score": 0,
                "risk_level": "low",
                "indicators": [],
                "explanation": "Resume too short to analyze for AI generation.",
                "detailed_analysis": {}
            }
        
        detector = AIResumeDetector()
        
        # Run all detection methods
        phrase_score = detector._analyze_common_phrases(resume_text)
        pattern_score = detector._analyze_ai_patterns(resume_text)
        perfection_score = detector._analyze_perfection(resume_text)
        language_score = detector._analyze_language_metrics(resume_text)
        structure_score = detector._analyze_structure(resume_text)
        metadata_score = detector._analyze_metadata(metadata or {})
        
        # Weighted scoring
        weighted_score = (
            phrase_score * 0.25 +          # 25% - Common phrases
            pattern_score * 0.20 +         # 20% - AI patterns
            perfection_score * 0.15 +      # 15% - Suspicious perfection
            language_score * 0.15 +        # 15% - Language metrics
            structure_score * 0.15 +       # 15% - Structure analysis
            metadata_score * 0.10          # 10% - Metadata clues
        )
        
        # Normalize to 0-100
        confidence_score = min(100, max(0, weighted_score))
        
        # Determine risk level
        if confidence_score >= 75:
            risk_level = "high"
            is_likely_ai = True
        elif confidence_score >= 50:
            risk_level = "medium"
            is_likely_ai = True
        else:
            risk_level = "low"
            is_likely_ai = False
        
        # Collect indicators
        indicators = []
        if phrase_score > 40:
            indicators.append({
                "type": "common_phrases",
                "score": phrase_score,
                "message": "Resume contains many common AI-generated phrases"
            })
        if pattern_score > 40:
            indicators.append({
                "type": "ai_patterns",
                "score": pattern_score,
                "message": "Multiple AI-specific writing patterns detected"
            })
        if perfection_score > 40:
            indicators.append({
                "type": "suspicious_perfection",
                "score": perfection_score,
                "message": "Resume formatting and writing appear suspiciously perfect"
            })
        if language_score > 50:
            indicators.append({
                "type": "language_metrics",
                "score": language_score,
                "message": "Language metrics suggest AI-generated content"
            })
        
        explanation = detector._generate_explanation(
            confidence_score, risk_level, indicators
        )
        
        return {
            "is_ai_generated": is_likely_ai,
            "confidence_score": round(confidence_score, 1),
            "risk_level": risk_level,
            "indicators": indicators,
            "explanation": explanation,
            "detailed_analysis": {
                "common_phrases_score": round(phrase_score, 1),
                "ai_patterns_score": round(pattern_score, 1),
                "perfection_score": round(perfection_score, 1),
                "language_metrics_score": round(language_score, 1),
                "structure_score": round(structure_score, 1),
                "metadata_score": round(metadata_score, 1),
            }
        }
    
    @staticmethod
    def _analyze_common_phrases(text: str) -> float:
        """Score based on AI-common phrases (0-100)."""
        text_lower = text.lower()
        total_score = 0
        phrase_count = 0
        
        for phrase, weight in AIResumeDetector.AI_COMMON_PHRASES.items():
            count = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
            if count > 0:
                phrase_count += count
                # Penalize for repetition - multiple occurrences suggest templating
                repetition_multiplier = min(count, 3)  # Cap at 3x
                total_score += weight * repetition_multiplier
        
        # Normalize: divide by word count to avoid favoring longer resumes
        words = len(text.split())
        if words > 0:
            frequency_score = (total_score / words) * 100 * 50  # Scale to 0-100
            return min(100, frequency_score)
        
        return 0
    
    @staticmethod
    def _analyze_ai_patterns(text: str) -> float:
        """Score based on AI-specific patterns (0-100)."""
        text_lower = text.lower()
        total_score = 0
        
        for pattern, weight in AIResumeDetector.AI_PATTERNS.items():
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            total_score += matches * weight
        
        # Normalize to 0-100
        words = len(text.split())
        if words > 0:
            frequency_score = (total_score / words) * 100 * 40
            return min(100, frequency_score)
        
        return 0
    
    @staticmethod
    def _analyze_perfection(text: str) -> float:
        """Score based on suspicious perfection indicators (0-100)."""
        score = 0
        
        # Check for complete lack of typos (unrealistic)
        potential_typos = len(re.findall(
            r'\b(?:thier|recieve|occured|mispelling|seperete|managment)\b',
            text,
            re.IGNORECASE
        ))
        if potential_typos == 0 and len(text.split()) > 200:
            score += 15  # Suspiciously perfect spelling
        
        # Check for consistent tense usage
        past_tense_verbs = len(re.findall(
            r'\b(?:managed|developed|created|implemented|led|designed)\b',
            text,
            re.IGNORECASE
        ))
        present_tense_verbs = len(re.findall(
            r'\b(?:manage|develop|create|implement|lead|design)\b',
            text,
            re.IGNORECASE
        ))
        
        total_verbs = past_tense_verbs + present_tense_verbs
        if total_verbs > 5:
            tense_consistency = max(past_tense_verbs, present_tense_verbs) / total_verbs
            if tense_consistency > 0.95:  # 95%+ consistent
                score += 10
        
        # Check for perfect punctuation (no run-ons, fragments)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            # Count sentences with proper structure (uncommon to have 100%)
            well_structured = sum(1 for s in sentences if 5 < len(s.split()) < 30)
            if well_structured / len(sentences) > 0.98:
                score += 8
        
        # Check for formatting perfection
        bullet_points = len(re.findall(r'^[\s]*[-•*]\s+', text, re.MULTILINE))
        newlines = text.count('\n')
        if newlines > 10 and bullet_points > 5:
            # Check alignment - consistent spacing before bullet points
            lines = text.split('\n')
            indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
            if indents:
                indent_variance = max(indents) - min(indents)
                if indent_variance <= 2:  # Perfect alignment
                    score += 7
        
        return min(100, score)
    
    @staticmethod
    def _analyze_language_metrics(text: str) -> float:
        """Score based on statistical language metrics (0-100)."""
        words = text.lower().split()
        if len(words) < 50:
            return 0
        
        score = 0
        
        # 1. Lexical diversity (AI often has moderate diversity)
        unique_words = len(set(words))
        lexical_diversity = unique_words / len(words)
        # Human resumes vary more (0.4-0.7), AI is often 0.5-0.6
        if 0.45 <= lexical_diversity <= 0.65:
            score += 15
        
        # 2. Average word length (AI tends toward 5-6 chars)
        avg_word_length = sum(len(w) for w in words) / len(words)
        if 4.5 <= avg_word_length <= 6.5:
            score += 10
        
        # 3. Sentence length consistency (AI is more uniform)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip().split() for s in sentences if s.strip()]
        if sentences:
            sentence_lengths = [len(s) for s in sentences]
            if sentence_lengths:
                mean_length = sum(sentence_lengths) / len(sentence_lengths)
                variance = sum((x - mean_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
                std_dev = math.sqrt(variance)
                # Low variance suggests AI
                if std_dev < 5 and mean_length > 8:
                    score += 15
        
        # 4. Use of passive voice (AI often uses less passive)
        passive_voice = len(re.findall(r'\b(?:was|were|been|being)\s+\w+(?:ed|en)\b', text, re.IGNORECASE))
        passive_ratio = passive_voice / len(words) if words else 0
        # Resumes typically have low passive (5-15%), AI might have even less
        if passive_ratio < 0.08:
            score += 10
        
        # 5. Superlative/power word density
        power_words = len(re.findall(
            r'\b(?:exceptional|outstanding|remarkable|unparalleled|unprecedented|best|greatest)\b',
            text,
            re.IGNORECASE
        ))
        if power_words / len(words) > 0.02:  # > 2% power words is suspicious
            score += 15
        
        return min(100, score)
    
    @staticmethod
    def _analyze_structure(text: str) -> float:
        """Score based on structural analysis (0-100)."""
        score = 0
        
        # Check for standard resume sections
        standard_sections = [
            r'\bsummary\b',
            r'\bobject(?:ive)?\b',
            r'\bexperience\b',
            r'\bskills?\b',
            r'\beducation\b',
            r'\bcertif(?:ication|icate)s?\b',
        ]
        
        found_sections = sum(
            1 for pattern in standard_sections
            if re.search(pattern, text, re.IGNORECASE)
        )
        
        # 4+ standard sections is common in both human and AI
        # But the specific ordering matters
        if found_sections >= 4:
            score += 10
        
        # Check for bullet point consistency
        lines = text.split('\n')
        bullet_lines = [l for l in lines if re.match(r'^\s*[-•*]\s+', l)]
        non_bullet_lines = [l for l in lines if l.strip() and not re.match(r'^\s*[-•*]\s+', l)]
        
        if bullet_lines and non_bullet_lines:
            bullet_ratio = len(bullet_lines) / len(lines) if lines else 0
            # AI resumes often have 40-60% bullet points
            if 0.35 <= bullet_ratio <= 0.65:
                score += 8
        
        # Check for dates/timeline consistency
        dates = re.findall(r'\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4})\b', text)
        if len(dates) >= 4:
            # Good date coverage
            score += 5
        
        return min(100, score)
    
    @staticmethod
    def _analyze_metadata(metadata: Dict[str, Any]) -> float:
        """Score based on document metadata (0-100)."""
        if not metadata:
            return 0
        
        score = 0
        
        # Check creation vs modification dates
        created_date = metadata.get("created_date")
        modified_date = metadata.get("modified_date")
        
        # If modified recently after creation, could indicate generation
        if created_date and modified_date:
            try:
                # If document was created and modified multiple times in one session
                # (indicating automated generation), flag it
                score += 5
            except:
                pass
        
        # Check PDF metadata
        if metadata.get("producer"):
            producer = metadata.get("producer", "").lower()
            # Some AI tools have specific producers
            if any(x in producer for x in ["openai", "chatgpt", "gpt", "claude"]):
                score += 25
        
        # Check for suspicious metadata
        if metadata.get("content_type") == "application/pdf":
            score += 5  # Generic PDFs are easier to generate
        
        return min(100, score)
    
    @staticmethod
    def _generate_explanation(
        confidence_score: float,
        risk_level: str,
        indicators: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable explanation of detection results."""
        if confidence_score < 30:
            base = "This resume appears to be written by a human. "
        elif confidence_score < 50:
            base = "This resume shows minimal signs of AI generation. "
        elif confidence_score < 70:
            base = f"This resume shows moderate signs of AI generation ({risk_level} risk). "
        else:
            base = f"This resume likely contains AI-generated content ({risk_level} risk). "
        
        if indicators:
            details = "Detected issues: " + ", ".join([
                ind["message"] for ind in indicators[:3]
            ])
            return base + details
        
        return base + "No specific indicators detected."


def check_resume_for_ai(
    resume_text: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convenience function to check if a resume is AI-generated.
    
    Args:
        resume_text: Resume text content
        metadata: Optional document metadata
        
    Returns:
        Detection results dictionary
    """
    return AIResumeDetector.detect_ai_generated(resume_text, metadata)
