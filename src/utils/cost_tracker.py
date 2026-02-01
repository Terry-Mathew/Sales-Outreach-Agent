"""
Cost Tracker - Monitors API usage and costs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class APICall:
    """Record of a single API call."""
    timestamp: float
    agent_name: str
    model: str
    cost: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class CostTracker:
    """
    Tracks API calls and estimates costs across the pipeline.
    Thread-safe for concurrent agent execution.
    """
    
    def __init__(self, max_cost_per_run: float = 0.50):
        self._calls: List[APICall] = []
        self._total_cost: float = 0.0
        self._max_cost = max_cost_per_run
        self._start_time: float = time.time()
    
    def add_call(
        self,
        agent_name: str,
        model: str = "gpt-4o-mini",
        cost: float = 0.002,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Record an API call with its cost."""
        call = APICall(
            timestamp=time.time(),
            agent_name=agent_name,
            model=model,
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=success,
            error=error
        )
        self._calls.append(call)
        self._total_cost += cost
    
    @property
    def call_count(self) -> int:
        """Total number of API calls."""
        return len(self._calls)
    
    @property
    def successful_calls(self) -> int:
        """Number of successful API calls."""
        return sum(1 for c in self._calls if c.success)
    
    @property
    def failed_calls(self) -> int:
        """Number of failed API calls."""
        return sum(1 for c in self._calls if not c.success)
    
    @property
    def total_cost(self) -> float:
        """Total estimated cost in USD."""
        return round(self._total_cost, 4)
    
    @property
    def is_over_budget(self) -> bool:
        """Check if we've exceeded the cost limit."""
        return self._total_cost >= self._max_cost
    
    @property
    def budget_remaining(self) -> float:
        """Remaining budget in USD."""
        return max(0, self._max_cost - self._total_cost)
    
    def get_calls_by_agent(self) -> Dict[str, int]:
        """Get call counts grouped by agent name."""
        counts: Dict[str, int] = {}
        for call in self._calls:
            counts[call.agent_name] = counts.get(call.agent_name, 0) + 1
        return counts
    
    def get_cost_by_agent(self) -> Dict[str, float]:
        """Get costs grouped by agent name."""
        costs: Dict[str, float] = {}
        for call in self._calls:
            costs[call.agent_name] = costs.get(call.agent_name, 0) + call.cost
        return {k: round(v, 4) for k, v in costs.items()}
    
    def summary(self) -> Dict:
        """
        Get a comprehensive summary of API usage.
        """
        duration = time.time() - self._start_time
        return {
            "calls": self.call_count,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "estimated_cost": self.total_cost,
            "budget_remaining": round(self.budget_remaining, 4),
            "over_budget": self.is_over_budget,
            "duration_seconds": round(duration, 2),
            "calls_by_agent": self.get_calls_by_agent(),
            "cost_by_agent": self.get_cost_by_agent(),
        }
    
    def reset(self) -> None:
        """Reset the tracker for a new run."""
        self._calls.clear()
        self._total_cost = 0.0
        self._start_time = time.time()


# Global singleton for backward compatibility
_global_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker()
    return _global_tracker


def reset_cost_tracker() -> None:
    """Reset the global cost tracker."""
    global _global_tracker
    if _global_tracker is not None:
        _global_tracker.reset()
