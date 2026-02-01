"""
Rule-Based Scorer - Objective scoring using configurable rules.
"""

from typing import Dict, List, Tuple
import re
from dataclasses import dataclass


@dataclass
class ScoringRule:
    """A single scoring rule with weight and evaluation function."""
    name: str
    max_points: int
    description: str


class RuleBasedScorer:
    """
    Enhanced rule-based email quality scorer.
    
    Evaluates emails against objective criteria like length,
    keyword presence, structure, and best practices.
    """
    
    # Spam trigger words to penalize
    SPAM_TRIGGERS = [
        "act now", "limited time", "urgent", "free", "guarantee",
        "no obligation", "winner", "congratulations", "click here",
        "buy now", "order now", "don't miss", "exclusive deal"
    ]
    
    # Power words that add value
    VALUE_KEYWORDS = [
        "increase", "reduce", "improve", "optimize", "automation",
        "efficiency", "save", "grow", "scale", "streamline",
        "accelerate", "transform", "revenue", "roi", "results"
    ]
    
    # Cliché openers to avoid
    BAD_OPENERS = [
        "i hope this email finds you well",
        "i hope this finds you well",
        "i'm reaching out",
        "just wanted to reach out",
        "i wanted to reach out",
        "touching base",
        "circling back",
        "following up"
    ]
    
    # Personalization indicators
    PERSONALIZATION_SIGNALS = [
        "your team", "your company", "your agency", "your business",
        "noticed", "saw that", "congrats on", "congratulations on",
        "i saw", "i noticed", "your recent"
    ]
    
    # CTA quality indicators
    CTA_KEYWORDS = [
        "schedule", "call", "chat", "15 minute", "15-minute",
        "quick call", "meet", "discuss", "talk", "connect",
        "available", "free for", "worth a"
    ]
    
    def __init__(self, max_score: int = 100):
        """Initialize scorer with maximum possible score."""
        self.max_score = max_score
    
    def score(self, subject: str, body: str) -> Dict:
        """
        Score an email using rule-based analysis.
        
        Args:
            subject: Email subject line
            body: Email body text
            
        Returns:
            Dict with total score and breakdown by category
        """
        breakdown = {}
        
        # 1. Length scoring (15 points)
        breakdown["length"] = self._score_length(body)
        
        # 2. Value proposition (20 points)
        breakdown["value_proposition"] = self._score_value_keywords(body)
        
        # 3. Personalization (15 points)
        breakdown["personalization"] = self._score_personalization(body)
        
        # 4. Opening quality (15 points)
        breakdown["opening_quality"] = self._score_opening(body)
        
        # 5. Structure (10 points)
        breakdown["structure"] = self._score_structure(body)
        
        # 6. CTA quality (15 points)
        breakdown["cta_quality"] = self._score_cta(body)
        
        # 7. Professionalism (10 points)
        breakdown["professionalism"] = self._score_professionalism(body)
        
        # 8. Subject line (bonus/penalty)
        breakdown["subject_line"] = self._score_subject(subject)
        
        # 9. Spam risk penalty
        spam_penalty = self._check_spam_triggers(subject, body)
        breakdown["spam_penalty"] = spam_penalty
        
        # Calculate total (capped at 0-100)
        raw_total = sum(breakdown.values())
        total = max(0, min(100, raw_total))
        
        return {
            "score": total,
            "breakdown": breakdown,
            "flags": self._get_flags(subject, body),
        }
    
    def _score_length(self, body: str) -> int:
        """Score based on email length (sweet spot: 80-150 words)."""
        words = len(body.split())
        
        if 80 <= words <= 150:
            return 15  # Perfect
        elif 60 <= words <= 180:
            return 12  # Good
        elif 40 <= words <= 220:
            return 8   # Acceptable
        elif words < 40:
            return 4   # Too short
        else:
            return 5   # Too long
    
    def _score_value_keywords(self, body: str) -> int:
        """Score presence of value-oriented language."""
        lower = body.lower()
        count = sum(1 for kw in self.VALUE_KEYWORDS if kw in lower)
        
        if count >= 4:
            return 20
        elif count >= 2:
            return 15
        elif count >= 1:
            return 10
        return 5
    
    def _score_personalization(self, body: str) -> int:
        """Score personalization signals."""
        lower = body.lower()
        signals = sum(1 for sig in self.PERSONALIZATION_SIGNALS if sig in lower)
        
        if signals >= 3:
            return 15
        elif signals >= 2:
            return 12
        elif signals >= 1:
            return 8
        return 3
    
    def _score_opening(self, body: str) -> int:
        """Score opening line quality (avoid clichés)."""
        lower = body.lower()[:200]  # Check first 200 chars
        
        # Penalize bad openers
        for opener in self.BAD_OPENERS:
            if opener in lower:
                return 3  # Heavy penalty for clichés
        
        # Bonus for starting with their name/company
        if body.strip().startswith("Hi ") or body.strip().startswith("Hey "):
            return 12  # Personalized greeting
        
        return 15  # No clichés found
    
    def _score_structure(self, body: str) -> int:
        """Score email structure and scannability."""
        score = 0
        
        # Check for paragraph breaks
        if "\n\n" in body or body.count('\n') >= 2:
            score += 4
        
        # Check for bullet points
        if any(c in body for c in ['•', '-', '*', '·']) and body.count('\n') >= 2:
            score += 3
        
        # Check paragraph count (2-4 is ideal)
        paragraphs = [p for p in body.split('\n\n') if p.strip()]
        if 2 <= len(paragraphs) <= 4:
            score += 3
        
        return min(10, score)
    
    def _score_cta(self, body: str) -> int:
        """Score call-to-action quality."""
        lower = body.lower()
        cta_count = sum(1 for kw in self.CTA_KEYWORDS if kw in lower)
        
        # Look for CTA in last portion of email
        last_third = lower[len(lower)*2//3:]
        has_cta_at_end = any(kw in last_third for kw in self.CTA_KEYWORDS)
        
        if cta_count >= 1 and has_cta_at_end:
            return 15
        elif cta_count >= 1:
            return 10
        return 5
    
    def _score_professionalism(self, body: str) -> int:
        """Score professional tone indicators."""
        score = 10
        
        # Penalize ALL CAPS words
        caps_words = len(re.findall(r'\b[A-Z]{3,}\b', body))
        if caps_words > 2:
            score -= 3
        
        # Penalize excessive exclamation marks
        exclamation_count = body.count('!')
        if exclamation_count > 2:
            score -= (exclamation_count - 2) * 2
        
        # Penalize too many "I" statements (self-focused)
        i_count = len(re.findall(r'\bI\b', body))
        if i_count > 5:
            score -= 2
        
        return max(0, score)
    
    def _score_subject(self, subject: str) -> int:
        """Score subject line quality."""
        score = 0
        
        # Length check (6-10 words ideal)
        words = len(subject.split())
        if 4 <= words <= 10:
            score += 5
        elif words > 12:
            score -= 5
        
        # Character count (under 60 ideal)
        if len(subject) <= 60:
            score += 3
        
        # Penalize ALL CAPS
        if subject.isupper():
            score -= 10
        
        # Penalize excessive punctuation
        if subject.count('!') > 1:
            score -= 5
        
        return score
    
    def _check_spam_triggers(self, subject: str, body: str) -> int:
        """Check for spam trigger words and return penalty."""
        combined = (subject + " " + body).lower()
        triggers_found = sum(1 for trigger in self.SPAM_TRIGGERS if trigger in combined)
        
        if triggers_found >= 3:
            return -20  # Heavy penalty
        elif triggers_found >= 1:
            return -10 * triggers_found
        return 0
    
    def _get_flags(self, subject: str, body: str) -> List[str]:
        """Get list of issues found in the email."""
        flags = []
        lower = body.lower()
        
        for opener in self.BAD_OPENERS:
            if opener in lower[:200]:
                flags.append(f"Cliché opener: '{opener}'")
                break
        
        words = len(body.split())
        if words > 200:
            flags.append(f"Too long ({words} words, target <150)")
        elif words < 50:
            flags.append(f"Too short ({words} words, target >80)")
        
        if body.count('!') > 2:
            flags.append("Too many exclamation marks")
        
        combined = (subject + " " + body).lower()
        for trigger in self.SPAM_TRIGGERS:
            if trigger in combined:
                flags.append(f"Spam trigger: '{trigger}'")
        
        return flags


# Backward compatibility alias
QualityScorer = RuleBasedScorer
