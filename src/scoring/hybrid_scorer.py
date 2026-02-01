"""
Hybrid Scorer - Combines rule-based and LLM scoring.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.scoring.rule_scorer import RuleBasedScorer
from src.scoring.llm_scorer import LLMScorer
from src.utils.logging import get_logger

logger = get_logger("hybrid_scorer")


class HybridScorer:
    """
    Hybrid email scoring combining rules and LLM evaluation.
    
    Uses configurable weights to blend objective rule-based scoring
    with subjective LLM-based quality assessment.
    """
    
    def __init__(
        self,
        rule_weight: float = 0.40,
        llm_weight: float = 0.60,
        llm_fallback_score: int = 50,
    ):
        """
        Initialize the hybrid scorer.
        
        Args:
            rule_weight: Weight for rule-based score (0-1)
            llm_weight: Weight for LLM score (0-1)
            llm_fallback_score: Score to use if LLM fails
        """
        if abs((rule_weight + llm_weight) - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0, got {rule_weight + llm_weight}"
            )
        
        self.rule_weight = rule_weight
        self.llm_weight = llm_weight
        self.rule_scorer = RuleBasedScorer()
        self.llm_scorer = LLMScorer(fallback_score=llm_fallback_score)
    
    async def score(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Score an email using both methods.
        
        Args:
            subject: Email subject line
            body: Email body text
            
        Returns:
            Dict with final score and detailed breakdown
        """
        # Get rule-based score
        rule_result = self.rule_scorer.score(subject, body)
        rule_score = rule_result["score"]
        
        logger.info(f"Rule-based score: {rule_score}")
        
        # Get LLM score
        llm_result = await self.llm_scorer.score(subject, body)
        llm_score = llm_result["score"]
        llm_success = llm_result.get("success", True)
        
        logger.info(f"LLM score: {llm_score} (success={llm_success})")
        
        # Calculate weighted final score
        final_score = int(
            rule_score * self.rule_weight + 
            llm_score * self.llm_weight
        )
        
        logger.info(
            f"Hybrid score: {final_score} "
            f"({self.rule_weight:.0%} rules + {self.llm_weight:.0%} LLM)"
        )
        
        return {
            "final_score": final_score,
            "rule_score": rule_score,
            "llm_score": llm_score,
            "llm_success": llm_success,
            "weights": {
                "rule": self.rule_weight,
                "llm": self.llm_weight,
            },
            "rule_breakdown": rule_result.get("breakdown", {}),
            "llm_breakdown": llm_result.get("dimension_breakdown"),
            "improvement_suggestions": llm_result.get("improvement_suggestions", []),
            "flags": rule_result.get("flags", []),
            "spam_risk": llm_result.get("spam_risk"),
            "predicted_response_rate": llm_result.get("predicted_response_rate"),
        }


# Module-level instance
_scorer: Optional[HybridScorer] = None


def get_hybrid_scorer() -> HybridScorer:
    """Get the global hybrid scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = HybridScorer(
            rule_weight=settings.rule_score_weight,
            llm_weight=settings.llm_score_weight,
            llm_fallback_score=settings.llm_fallback_score,
        )
    return _scorer


async def hybrid_score_email(subject: str, body: str) -> Dict[str, Any]:
    """
    Convenience function to score an email with hybrid method.
    
    Args:
        subject: Email subject line
        body: Email body text
        
    Returns:
        Scoring result dictionary
    """
    scorer = get_hybrid_scorer()
    return await scorer.score(subject, body)
