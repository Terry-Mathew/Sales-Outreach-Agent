"""
FastAPI Application - REST API for the Sales Outreach Agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.pipeline import run_sales_pipeline, PipelineResult, DraftResult


# ========================================
# Request/Response Models
# ========================================

class GenerateRequest(BaseModel):
    """Request to generate sales outreach emails."""
    prospect_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of the target prospect",
        examples=["CEO of a 50-person marketing agency looking to automate client reporting"]
    )
    generate_subjects: bool = Field(
        default=True,
        description="Whether to generate subject lines for each email"
    )


class DraftResponse(BaseModel):
    """A single email draft with scoring."""
    agent_name: str
    agent_index: int
    subject: Optional[str]
    body: str
    final_score: int
    rule_score: int
    llm_score: int
    improvement_suggestions: List[str]
    success: bool


class CostResponse(BaseModel):
    """Cost tracking information."""
    api_calls: int
    estimated_cost_usd: float
    duration_seconds: float
    calls_by_agent: Dict[str, int]


class GenerateResponse(BaseModel):
    """Response containing all generated emails and winner."""
    success: bool
    chosen_agent: str
    chosen_agent_index: int
    winning_score: int
    winning_subject: Optional[str]
    winning_body: str
    all_drafts: List[DraftResponse]
    costs: CostResponse


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    company: str


# ========================================
# API Application
# ========================================

def create_api() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=f"{settings.company_name} Sales Agent API",
        description="Generate high-quality sales outreach emails using multi-agent AI",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ========================================
    # Endpoints
    # ========================================
    
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Check if the API is running."""
        return HealthResponse(
            status="healthy",
            version="2.0.0",
            company=settings.company_name
        )
    
    @app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
    async def generate_emails(request: GenerateRequest):
        """
        Generate sales outreach emails for a prospect.
        
        This endpoint:
        1. Creates multiple email drafts using different AI personas
        2. Generates subject lines for each draft
        3. Scores each draft using a hybrid rules + LLM approach
        4. Returns all drafts ranked by score with the winner highlighted
        """
        try:
            # Run the pipeline
            result: PipelineResult = await run_sales_pipeline(
                prospect_description=request.prospect_description,
                generate_subjects=request.generate_subjects,
            )
            
            # Convert drafts to response format
            drafts = []
            for draft in result.all_drafts:
                score = draft.score or {}
                drafts.append(DraftResponse(
                    agent_name=draft.agent_name,
                    agent_index=draft.agent_index,
                    subject=draft.subject,
                    body=draft.text,
                    final_score=score.get("final_score", 0),
                    rule_score=score.get("rule_score", 0),
                    llm_score=score.get("llm_score", 0),
                    improvement_suggestions=score.get("improvement_suggestions", []),
                    success=draft.success,
                ))
            
            # Build cost response
            costs = result.costs
            cost_response = CostResponse(
                api_calls=costs.get("calls", 0),
                estimated_cost_usd=costs.get("estimated_cost", 0),
                duration_seconds=costs.get("duration_seconds", 0),
                calls_by_agent=costs.get("calls_by_agent", {}),
            )
            
            return GenerateResponse(
                success=True,
                chosen_agent=result.chosen_agent,
                chosen_agent_index=result.chosen_agent_index,
                winning_score=result.winning_score,
                winning_subject=result.winning_subject,
                winning_body=result.winning_draft,
                all_drafts=drafts,
                costs=cost_response,
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate emails: {str(e)}"
            )
    
    @app.get("/agents", tags=["Info"])
    async def list_agents():
        """List available SDR agent personas."""
        return {
            "agents": [
                {
                    "name": "Professional",
                    "description": "Value-focused, ROI-driven approach",
                    "style": "Formal, outcome-oriented",
                    "ideal_for": "C-suite executives, enterprise prospects"
                },
                {
                    "name": "Engaging",
                    "description": "Pattern-interrupt style with personality",
                    "style": "Conversational, light humor",
                    "ideal_for": "Startup founders, marketing teams"
                },
                {
                    "name": "Concise",
                    "description": "Ultra-brief, bullet-point format",
                    "style": "Direct, scannable",
                    "ideal_for": "Busy executives with overflowing inboxes"
                }
            ]
        }
    
    return app


# Create app instance for uvicorn
api = create_api()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:api",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
