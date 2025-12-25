"""
TMP AI Consulting - Sales Automation Agent (Hybrid Scoring Version)
Generates multiple cold outreach drafts using agent personalities,
scores them using both RULES & LLM JUDGE, and returns structured output.
"""

from dotenv import load_dotenv
load_dotenv(override=True)

from agents import Agent, Runner, trace, function_tool
from pydantic import BaseModel, Field
from typing import Dict, Optional
import asyncio
import time
import json
import re

# ---------------------------
# Utilities: CostTracker, Cache, Memory
# ---------------------------
class CostTracker:
    def __init__(self):
        self.calls = 0
        self.estimated_cost = 0.0

    def add_call(self, cost: float = 0.0):
        self.calls += 1
        self.estimated_cost += cost

    def summary(self):
        return {"calls": self.calls, "estimated_cost": round(self.estimated_cost, 4)}


class SimpleCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = {"value": value, "ts": time.time()}

cache = SimpleCache()
costs = CostTracker()

class AgentMemory:
    def __init__(self):
        self.history = []

    def remember(self, record: dict):
        self.history.append({**record, "ts": time.time()})

memory = AgentMemory()

# ---------------------------
# LLM Judge Output Schema
# ---------------------------
class LLMEmailScore(BaseModel):
    total_score: int = Field(description="Final score from 0–100")
    reasoning: str = Field(description="Why the email received this score")

# ---------------------------
# LLM Judge Agent
# ---------------------------
email_judge = Agent(
    name="EmailJudge",
    instructions="""
You are an expert email evaluator. Score the email from 0–100 using this weighted rubric:
- Clarity (20%)
- Value Proposition (20%)
- Relevance to Prospect (15%)
- Persuasiveness (15%)
- Personalization (10%)
- Precision & Professionalism (10%)
- Structure / Readability (10%)
Return JSON: { "total_score": int, "reasoning": "..." }
""",
    model="gpt-4o-mini",
    output_type=LLMEmailScore
)

# ---------------------------
# RULE-BASED SCORING
# ---------------------------
class QualityScorer:

    @staticmethod
    def score_rules(subject: str, body: str):
        score = 0
        max_score = 70
        body_lower = body.lower()
        words = len(body.split())

        # 1. Clarity (sweet spot for emails)
        if 60 <= words <= 180:
            score += 10
        elif 40 <= words <= 220:
            score += 7
        else:
            score += 4

        # 2. Value proposition keywords
        if any(term in body_lower for term in [
            "increase", "reduce", "improve", "optimize", "automation", "agentic", "efficiency"
        ]):
            score += 10

        # 3. Relevance / role alignment
        if any(term in body_lower for term in ["your team", "your agency", "as the ceo", "marketing team"]):
            score += 10

        # 4. Persuasiveness
        if any(term in body_lower for term in ["imagine", "picture this", "what if", "you could"]):
            score += 7

        # 5. Personalization
        if "[your" not in body_lower:
            score += 5

        # 6. Precision / professionalism
        capitalized = re.findall(r'[A-Z][a-z]+', body)
        if len(capitalized) >= 5:
            score += 7

        # 7. Structure
        if "\n\n" in body:
            score += 5

        # 8. CTA Quality
        if any(term in body_lower for term in ["schedule", "call", "quick chat", "available", "meet"]):
            score += 8

        # Normalize
        rule_score = int((score / max_score) * 100)
        return max(0, min(100, rule_score))

# ---------------------------
# HYBRID SCORING COMBINER
# ---------------------------
async def hybrid_score_email(subject: str, body: str):
    # RULE SCORE
    rule_score = QualityScorer.score_rules(subject, body)

    # LLM SCORE (fallback safe)
    try:
        judge_result = await Runner.run(email_judge, f"Subject:\n{subject}\n\nBody:\n{body}")
        llm_score = judge_result.final_output.total_score
    except Exception:
        llm_score = 50  # fallback

    # Hybrid weighted scoring
    final_score = int(rule_score * 0.40 + llm_score * 0.60)

    return {
        "final_score": final_score,
        "rule_score": rule_score,
        "llm_score": llm_score
    }

# ---------------------------
# TMP AI Consulting Prompts
# ---------------------------
company_name = "TMP AI Consulting"

instructions_professional = f"""You are a Professional SDR at {company_name}.
Write a professional, outcome-focused cold outreach email.
Focus on agentic AI, automation, efficiency, cost savings, and revenue impact.
Keep paragraphs short. Include one CTA. ~150 words max."""

instructions_engaging = f"""You are an Engaging SDR at {company_name}.
Write a personality-driven, clever outreach email using light humor and pattern-interrupts.
Focus on capturing attention while maintaining professionalism. ~180 words."""

instructions_concise = f"""You are a Concise SDR at {company_name}.
Write an ultra-brief outreach email for busy executives. Bullets allowed. ~100 words."""

sales_agent_prof = Agent(name="TMPAI_Professional", instructions=instructions_professional, model="gpt-4o-mini")
sales_agent_eng = Agent(name="TMPAI_Engaging", instructions=instructions_engaging, model="gpt-4o-mini")
sales_agent_conc = Agent(name="TMPAI_Concise", instructions=instructions_concise, model="gpt-4o-mini")

# ---------------------------
# Subject Writer (used later)
# ---------------------------
subject_writer = Agent(
    name="SubjectWriter",
    instructions="Write a concise, curiosity-driven subject line under 60 characters.",
    model="gpt-4o-mini"
)

# ---------------------------
# Runner helper
# ---------------------------
async def safe_run(agent: Agent, prompt: str):
    try:
        res = await Runner.run(agent, prompt)
        costs.add_call(0.002)
        return res
    except:
        return None

# ---------------------------
# MAIN ORCHESTRATION PIPELINE
# ---------------------------
async def run_tmpai_sales(task_description: str, human_approval: bool = False):

    # 1. Generate drafts
    drafts = await asyncio.gather(
        safe_run(sales_agent_prof, task_description),
        safe_run(sales_agent_eng, task_description),
        safe_run(sales_agent_conc, task_description),
    )

    cleaned = []
    for i, d in enumerate(drafts, start=1):
        if d is None:
            cleaned.append({"agent": i, "text": ""})
        else:
            text = getattr(d, "final_output", None) or getattr(d, "output", None) or str(d)
            cleaned.append({"agent": i, "text": text})

    # 2. Hybrid Scoring
    scored = []
    for d in cleaned:
        subject = "Agentic AI to help your team"  # temporary subject for scoring
        s = await hybrid_score_email(subject, d["text"])
        scored.append({"agent_index": d["agent"], "text": d["text"], "score": s})

    # 3. Winner
    best = max(scored, key=lambda x: x["score"]["final_score"])

    return {
        "chosen_agent": best["agent_index"],
        "score": best["score"]["final_score"],
        "scored_details": scored,
        "costs": costs.summary()
    }

