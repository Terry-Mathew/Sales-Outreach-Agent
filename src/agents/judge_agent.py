"""
Email Judge Agent - Evaluates email quality using LLM.
"""

from agents import Agent
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings


class DimensionBreakdown(BaseModel):
    """Detailed breakdown of scores by dimension."""
    clarity: int = Field(ge=0, le=100, description="Clarity score 0-100")
    value_proposition: int = Field(ge=0, le=100, description="Value proposition score")
    relevance: int = Field(ge=0, le=100, description="Relevance to prospect score")
    persuasiveness: int = Field(ge=0, le=100, description="Persuasiveness score")
    personalization: int = Field(ge=0, le=100, description="Personalization score")
    professionalism: int = Field(ge=0, le=100, description="Professionalism score")
    structure: int = Field(ge=0, le=100, description="Structure/readability score")


class LLMEmailScore(BaseModel):
    """Structured output for email evaluation."""
    total_score: int = Field(
        ge=0, 
        le=100, 
        description="Final weighted score from 0-100"
    )
    reasoning: str = Field(
        description="2-3 sentences explaining key factors that influenced the score"
    )
    dimension_breakdown: Optional[DimensionBreakdown] = Field(
        default=None,
        description="Detailed scores by evaluation dimension"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Specific, actionable suggestions to improve the email"
    )
    spam_risk: Optional[str] = Field(
        default=None,
        description="Spam risk level: low, medium, or high"
    )
    predicted_response_rate: Optional[str] = Field(
        default=None,
        description="Estimated response rate percentage"
    )


def load_judge_prompt() -> str:
    """Load the email judge prompt template."""
    prompt_path = settings.prompts_dir / "email_judge.md"
    
    if not prompt_path.exists():
        # Fallback to basic prompt if file not found
        return """
You are an expert email evaluator. Score the email from 0-100 using this weighted rubric:
- Clarity (20%)
- Value Proposition (20%)
- Relevance to Prospect (15%)
- Persuasiveness (15%)
- Personalization (10%)
- Precision & Professionalism (10%)
- Structure / Readability (10%)

Return JSON with total_score and reasoning.
"""
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_email_judge() -> Agent:
    """
    Get the Email Judge agent.
    
    This agent evaluates email drafts using a comprehensive rubric
    and provides structured scoring with detailed feedback.
    
    Returns:
        Configured Agent instance for email evaluation
    """
    prompt = load_judge_prompt()
    
    return Agent(
        name="EmailJudge",
        instructions=prompt,
        model=settings.judge_model,
        output_type=LLMEmailScore,
    )


def format_email_for_judge(subject: str, body: str) -> str:
    """
    Format an email for evaluation by the judge.
    
    Args:
        subject: Email subject line
        body: Email body text
        
    Returns:
        Formatted string for the judge agent
    """
    return f"""
Subject:
{subject}

Body:
{body}
"""


# Pre-create judge agent for easy import
try:
    email_judge = get_email_judge()
except Exception:
    email_judge = None
