"""
Sales Outreach Pipeline Orchestrator - Main entry point for email generation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from agents import Agent, Runner
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.agents.sdr_agents import (
    get_professional_agent,
    get_engaging_agent,
    get_concise_agent,
    load_prompt,
)
from src.agents.subject_agent import get_subject_writer
from src.scoring.hybrid_scorer import hybrid_score_email
from src.utils.cost_tracker import CostTracker, get_cost_tracker
from src.utils.memory import AgentMemory, get_memory
from src.utils.logging import get_logger, log_pipeline

logger = get_logger("pipeline")


@dataclass
class DraftResult:
    """Result from a single agent's draft generation."""
    agent_name: str
    agent_index: int
    text: str
    subject: Optional[str] = None
    score: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete result from the sales outreach pipeline."""
    chosen_agent: str
    chosen_agent_index: int
    winning_score: int
    winning_draft: str
    winning_subject: Optional[str]
    all_drafts: List[DraftResult]
    costs: Dict[str, Any]
    memory_stats: Dict[str, Any] = field(default_factory=dict)


class SalesOutreachPipeline:
    """
    Orchestrates the multi-agent sales email generation pipeline.
    
    Flow:
    1. Generate drafts from all SDR agents in parallel
    2. Generate subject lines for each draft
    3. Score each draft using hybrid scoring
    4. Select the best performing draft
    5. Track costs and update memory
    """
    
    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        memory: Optional[AgentMemory] = None,
    ):
        """
        Initialize the pipeline.
        
        Args:
            cost_tracker: Optional cost tracker instance
            memory: Optional memory instance
        """
        self.cost_tracker = cost_tracker or get_cost_tracker()
        self.memory = memory or get_memory()
        self._subject_writer = None
    
    @property
    def subject_writer(self):
        """Lazy-load subject writer agent."""
        if self._subject_writer is None:
            self._subject_writer = get_subject_writer()
        return self._subject_writer
    
    async def _run_agent(
        self,
        agent: Agent,
        prompt: str,
        agent_name: str,
        agent_index: int,
    ) -> DraftResult:
        """
        Run a single agent with error handling.
        
        Args:
            agent: Agent to run
            prompt: Prompt to send
            agent_name: Name for logging
            agent_index: Index for identification
            
        Returns:
            DraftResult with generated text or error
        """
        try:
            logger.debug(f"Running agent: {agent_name}")
            
            result = await Runner.run(agent, prompt)
            
            # Track cost
            self.cost_tracker.add_call(
                agent_name=agent_name,
                model=settings.primary_model,
                cost=settings.estimated_cost_per_call,
            )
            
            # Extract text from result
            text = getattr(result, "final_output", None)
            if text is None:
                text = getattr(result, "output", None)
            if text is None:
                text = str(result)
            
            logger.info(f"Agent {agent_name} generated {len(text)} chars")
            
            return DraftResult(
                agent_name=agent_name,
                agent_index=agent_index,
                text=text,
                success=True,
            )
            
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            
            self.cost_tracker.add_call(
                agent_name=agent_name,
                model=settings.primary_model,
                cost=0,  # No cost on failure
                success=False,
                error=str(e),
            )
            
            return DraftResult(
                agent_name=agent_name,
                agent_index=agent_index,
                text="",
                success=False,
                error=str(e),
            )
    
    async def _generate_subject(self, body: str) -> Optional[str]:
        """
        Generate a subject line for an email body.
        
        Args:
            body: Email body text
            
        Returns:
            Generated subject line or None on failure
        """
        try:
            # Truncate body for subject generation
            context = body[:500] if len(body) > 500 else body
            
            result = await Runner.run(self.subject_writer, context)
            
            self.cost_tracker.add_call(
                agent_name="SubjectWriter",
                model=settings.primary_model,
                cost=settings.estimated_cost_per_call * 0.5,  # Shorter call
            )
            
            subject = getattr(result, "final_output", str(result))
            
            # Clean up subject (remove quotes, extra whitespace)
            subject = subject.strip().strip('"\'')
            
            return subject
            
        except Exception as e:
            logger.error(f"Subject generation failed: {e}")
            return None
    
    def _create_prompt_with_context(
        self,
        base_template: str,
        prospect_description: str,
    ) -> str:
        """
        Create a complete prompt with prospect context.
        
        Args:
            base_template: Base prompt template
            prospect_description: Description of the prospect
            
        Returns:
            Formatted prompt
        """
        return base_template.format(
            company_name=settings.company_name,
            prospect_description=prospect_description,
        )
    
    async def run(
        self,
        prospect_description: str,
        generate_subjects: bool = True,
    ) -> PipelineResult:
        """
        Run the complete sales outreach pipeline.
        
        Args:
            prospect_description: Description of the target prospect
            generate_subjects: Whether to generate subject lines
            
        Returns:
            PipelineResult with all drafts and winner
        """
        log_pipeline(logger, "START", f"Prospect: {prospect_description[:50]}...")
        
        # Reset cost tracker for this run
        self.cost_tracker.reset()
        
        # ========================================
        # Stage 1: Generate drafts in parallel
        # ========================================
        log_pipeline(logger, "DRAFT_GENERATION", "Starting parallel generation")
        
        # Load prompts and create formatted versions
        professional_prompt = load_prompt("professional_sdr.md")
        engaging_prompt = load_prompt("engaging_sdr.md")
        concise_prompt = load_prompt("concise_sdr.md")
        
        # Create agents with specific prompts
        agents_and_prompts = [
            (get_professional_agent(), self._create_prompt_with_context(
                professional_prompt, prospect_description), "Professional", 1),
            (get_engaging_agent(), self._create_prompt_with_context(
                engaging_prompt, prospect_description), "Engaging", 2),
            (get_concise_agent(), self._create_prompt_with_context(
                concise_prompt, prospect_description), "Concise", 3),
        ]
        
        # Run all agents in parallel
        draft_tasks = [
            self._run_agent(agent, prompt, name, idx)
            for agent, prompt, name, idx in agents_and_prompts
        ]
        drafts: List[DraftResult] = await asyncio.gather(*draft_tasks)
        
        log_pipeline(
            logger, 
            "DRAFT_GENERATION", 
            f"Generated {sum(1 for d in drafts if d.success)} drafts"
        )
        
        # ========================================
        # Stage 2: Generate subjects (optional)
        # ========================================
        if generate_subjects:
            log_pipeline(logger, "SUBJECT_GENERATION", "Generating subject lines")
            
            for draft in drafts:
                if draft.success and draft.text:
                    subject = await self._generate_subject(draft.text)
                    draft.subject = subject or "AI automation for your team"
                else:
                    draft.subject = "AI automation for your team"
        else:
            for draft in drafts:
                draft.subject = "AI automation for your team"
        
        # ========================================
        # Stage 3: Score all drafts
        # ========================================
        log_pipeline(logger, "SCORING", "Hybrid scoring all drafts")
        
        for draft in drafts:
            if draft.success and draft.text:
                score = await hybrid_score_email(draft.subject, draft.text)
                draft.score = score
                
                # Track cost for judge call
                self.cost_tracker.add_call(
                    agent_name="EmailJudge",
                    model=settings.judge_model,
                    cost=settings.estimated_cost_per_call,
                )
                
                # Remember in memory
                self.memory.remember(
                    event_type="email_scored",
                    agent_name=draft.agent_name,
                    score=score["final_score"],
                    data={
                        "prospect": prospect_description[:100],
                        "rule_score": score["rule_score"],
                        "llm_score": score["llm_score"],
                    }
                )
            else:
                draft.score = {"final_score": 0, "rule_score": 0, "llm_score": 0}
        
        # ========================================
        # Stage 4: Select winner
        # ========================================
        log_pipeline(logger, "SELECTION", "Choosing best draft")
        
        # Sort by score and pick the best
        scored_drafts = [d for d in drafts if d.score]
        best_draft = max(
            scored_drafts,
            key=lambda d: d.score["final_score"],
            default=drafts[0] if drafts else None
        )
        
        if best_draft:
            logger.info(
                f"Winner: {best_draft.agent_name} with score "
                f"{best_draft.score['final_score']}"
            )
        
        # ========================================
        # Stage 5: Compile results
        # ========================================
        log_pipeline(logger, "COMPLETE", f"Pipeline finished")
        
        return PipelineResult(
            chosen_agent=best_draft.agent_name if best_draft else "Unknown",
            chosen_agent_index=best_draft.agent_index if best_draft else 0,
            winning_score=best_draft.score["final_score"] if best_draft else 0,
            winning_draft=best_draft.text if best_draft else "",
            winning_subject=best_draft.subject if best_draft else None,
            all_drafts=drafts,
            costs=self.cost_tracker.summary(),
            memory_stats=self.memory.get_agent_stats(),
        )


async def run_sales_pipeline(
    prospect_description: str,
    generate_subjects: bool = True,
) -> PipelineResult:
    """
    Convenience function to run the sales pipeline.
    
    Args:
        prospect_description: Description of the target prospect
        generate_subjects: Whether to generate subject lines
        
    Returns:
        PipelineResult with all drafts and winner
    """
    pipeline = SalesOutreachPipeline()
    return await pipeline.run(prospect_description, generate_subjects)
