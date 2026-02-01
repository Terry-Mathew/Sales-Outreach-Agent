"""
SDR Agents - Sales Development Representative agents with different personas.
"""

from agents import Agent
from pathlib import Path
from typing import List, Tuple
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings


def load_prompt(filename: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        filename: Name of the prompt file (e.g., 'professional_sdr.md')
        
    Returns:
        Prompt template as string
    """
    prompt_path = settings.prompts_dir / filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def format_prompt(template: str, prospect_description: str) -> str:
    """
    Format a prompt template with context.
    
    Args:
        template: Prompt template with placeholders
        prospect_description: Description of the prospect
        
    Returns:
        Formatted prompt
    """
    return template.format(
        company_name=settings.company_name,
        prospect_description=prospect_description,
    )


def get_professional_agent() -> Agent:
    """
    Get the Professional SDR agent.
    
    This agent writes professional, outcome-focused cold outreach emails
    with emphasis on value, efficiency, and ROI.
    """
    template = load_prompt("professional_sdr.md")
    
    return Agent(
        name="TMPAI_Professional",
        instructions=template.format(
            company_name=settings.company_name,
            prospect_description="{prospect_description}",  # Placeholder for runtime
        ),
        model=settings.primary_model,
    )


def get_engaging_agent() -> Agent:
    """
    Get the Engaging SDR agent.
    
    This agent uses pattern interrupts, light humor, and conversational tone
    to stand out in crowded inboxes.
    """
    template = load_prompt("engaging_sdr.md")
    
    return Agent(
        name="TMPAI_Engaging",
        instructions=template.format(
            company_name=settings.company_name,
            prospect_description="{prospect_description}",
        ),
        model=settings.primary_model,
    )


def get_concise_agent() -> Agent:
    """
    Get the Concise SDR agent.
    
    This agent writes ultra-brief emails for busy executives,
    using bullet points and minimal words.
    """
    template = load_prompt("concise_sdr.md")
    
    return Agent(
        name="TMPAI_Concise",
        instructions=template.format(
            company_name=settings.company_name,
            prospect_description="{prospect_description}",
        ),
        model=settings.primary_model,
    )


def create_sdr_agents() -> List[Tuple[str, Agent]]:
    """
    Create all SDR agents.
    
    Returns:
        List of (agent_name, agent) tuples
    """
    return [
        ("Professional", get_professional_agent()),
        ("Engaging", get_engaging_agent()),
        ("Concise", get_concise_agent()),
    ]


# Pre-create agents for easy import
# Note: These use the default model from settings
try:
    professional_agent = get_professional_agent()
    engaging_agent = get_engaging_agent()
    concise_agent = get_concise_agent()
except Exception:
    # Allow import to succeed even if prompts not found yet
    professional_agent = None
    engaging_agent = None
    concise_agent = None
