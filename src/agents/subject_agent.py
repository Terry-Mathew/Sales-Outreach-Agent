"""
Subject Writer Agent - Generates optimized email subject lines.
"""

from agents import Agent
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings


def load_subject_prompt() -> str:
    """Load the subject writer prompt template."""
    prompt_path = settings.prompts_dir / "subject_writer.md"
    
    if not prompt_path.exists():
        # Fallback to basic prompt
        return """
You are a subject line optimization specialist. Generate a compelling, 
curiosity-driven email subject line.

Rules:
- 6-10 words maximum (under 60 characters)
- Create genuine curiosity without clickbait
- NO spam trigger words
- NO all caps or excessive punctuation

Output ONLY the subject line, nothing else.
"""
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_subject_writer() -> Agent:
    """
    Get the Subject Writer agent.
    
    This agent generates optimized subject lines for email drafts,
    focusing on curiosity without spam triggers.
    
    Returns:
        Configured Agent instance for subject line generation
    """
    prompt = load_subject_prompt()
    
    return Agent(
        name="SubjectWriter",
        instructions=prompt,
        model=settings.primary_model,
    )


def format_body_for_subject(body: str, max_chars: int = 500) -> str:
    """
    Format email body for subject line generation.
    
    Args:
        body: Full email body
        max_chars: Maximum characters to send for context
        
    Returns:
        Truncated body suitable for subject generation
    """
    # Take first portion of body for context
    truncated = body[:max_chars]
    
    # Try to end at a sentence boundary
    if len(body) > max_chars:
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        cut_point = max(last_period, last_newline)
        if cut_point > max_chars // 2:
            truncated = truncated[:cut_point + 1]
    
    return truncated


# Pre-create agent for easy import
try:
    subject_writer = get_subject_writer()
except Exception:
    subject_writer = None
