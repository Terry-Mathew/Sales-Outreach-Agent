"""
LLM Scorer - Qualitative email scoring using language model judge.
"""

from typing import Optional, Dict, Any
from agents import Runner
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.agents.judge_agent import get_email_judge, format_email_for_judge, LLMEmailScore
from src.utils.logging import get_logger

logger = get_logger("llm_scorer")


class LLMScorer:
    """
    LLM-based email quality scorer.
    
    Uses a language model to evaluate emails on subjective criteria
    like persuasiveness, tone, and overall quality.
    """
    
    def __init__(self, fallback_score: int = 50):
        """
        Initialize the LLM scorer.
        
        Args:
            fallback_score: Score to use if LLM evaluation fails
        """
        self.fallback_score = fallback_score
        self._judge = None
    
    @property
    def judge(self):
        """Lazy-load the judge agent."""
        if self._judge is None:
            self._judge = get_email_judge()
        return self._judge
    
    async def score(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Score an email using the LLM judge.
        
        Args:
            subject: Email subject line
            body: Email body text
            
        Returns:
            Dict with score and detailed breakdown
        """
        try:
            # Format the email for the judge
            formatted = format_email_for_judge(subject, body)
            
            logger.debug(f"Sending email to LLM judge for evaluation")
            
            # Run the judge agent
            result = await Runner.run(self.judge, formatted)
            
            # Extract the structured output
            output: LLMEmailScore = result.final_output
            
            logger.info(
                f"LLM Judge Score: {output.total_score} | "
                f"Spam Risk: {output.spam_risk or 'not evaluated'}"
            )
            
            return {
                "score": output.total_score,
                "reasoning": output.reasoning,
                "dimension_breakdown": (
                    output.dimension_breakdown.model_dump() 
                    if output.dimension_breakdown else None
                ),
                "improvement_suggestions": output.improvement_suggestions,
                "spam_risk": output.spam_risk,
                "predicted_response_rate": output.predicted_response_rate,
                "success": True,
            }
            
        except Exception as e:
            logger.error(f"LLM scoring failed: {e}")
            
            return {
                "score": self.fallback_score,
                "reasoning": f"Fallback score used due to evaluation error: {str(e)}",
                "dimension_breakdown": None,
                "improvement_suggestions": [],
                "spam_risk": None,
                "predicted_response_rate": None,
                "success": False,
                "error": str(e),
            }
    
    async def batch_score(
        self, 
        emails: list[tuple[str, str]]
    ) -> list[Dict[str, Any]]:
        """
        Score multiple emails.
        
        Args:
            emails: List of (subject, body) tuples
            
        Returns:
            List of score dictionaries
        """
        results = []
        for subject, body in emails:
            result = await self.score(subject, body)
            results.append(result)
        return results


# Module-level instance for easy access
_scorer: Optional[LLMScorer] = None


def get_llm_scorer() -> LLMScorer:
    """Get the global LLM scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = LLMScorer(fallback_score=settings.llm_fallback_score)
    return _scorer
