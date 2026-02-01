"""
Agent Memory - Persistent memory for learning from past runs.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import time
import json
from pathlib import Path


@dataclass
class MemoryRecord:
    """A single memory record."""
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    agent_name: Optional[str] = None
    score: Optional[float] = None
    tags: List[str] = field(default_factory=list)


class AgentMemory:
    """
    Memory system for tracking agent performance and learning from past runs.
    Can be used to improve prompts and identify patterns over time.
    """
    
    def __init__(self, persist_path: Optional[Path] = None, max_records: int = 1000):
        """
        Initialize memory.
        
        Args:
            persist_path: Optional path to persist memory to disk
            max_records: Maximum records to keep in memory
        """
        self._history: List[MemoryRecord] = []
        self._persist_path = persist_path
        self._max_records = max_records
        
        # Load from disk if path exists
        if persist_path and persist_path.exists():
            self._load()
    
    def remember(
        self,
        event_type: str,
        data: Dict[str, Any],
        agent_name: Optional[str] = None,
        score: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Record an event to memory.
        
        Args:
            event_type: Type of event (e.g., 'draft_generated', 'email_scored')
            data: Event data
            agent_name: Name of the agent involved
            score: Optional score associated with this event
            tags: Optional tags for categorization
        """
        record = MemoryRecord(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            agent_name=agent_name,
            score=score,
            tags=tags or []
        )
        self._history.append(record)
        
        # Trim if over capacity
        if len(self._history) > self._max_records:
            self._history = self._history[-self._max_records:]
        
        # Persist if path configured
        if self._persist_path:
            self._save()
    
    def recall(
        self,
        event_type: Optional[str] = None,
        agent_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_score: Optional[float] = None,
        limit: int = 10
    ) -> List[MemoryRecord]:
        """
        Recall records matching the given criteria.
        
        Args:
            event_type: Filter by event type
            agent_name: Filter by agent name
            tags: Filter by tags (records must have ALL specified tags)
            min_score: Filter by minimum score
            limit: Maximum records to return
            
        Returns:
            List of matching records, most recent first
        """
        results = []
        
        for record in reversed(self._history):
            if event_type and record.event_type != event_type:
                continue
            if agent_name and record.agent_name != agent_name:
                continue
            if tags and not all(t in record.tags for t in tags):
                continue
            if min_score is not None and (record.score is None or record.score < min_score):
                continue
            
            results.append(record)
            if len(results) >= limit:
                break
        
        return results
    
    def get_best_performing_agent(self, event_type: str = "email_scored") -> Optional[str]:
        """
        Get the agent with the highest average score.
        
        Returns:
            Agent name or None if no data
        """
        agent_scores: Dict[str, List[float]] = {}
        
        for record in self._history:
            if record.event_type == event_type and record.agent_name and record.score:
                if record.agent_name not in agent_scores:
                    agent_scores[record.agent_name] = []
                agent_scores[record.agent_name].append(record.score)
        
        if not agent_scores:
            return None
        
        # Calculate averages
        averages = {
            name: sum(scores) / len(scores)
            for name, scores in agent_scores.items()
        }
        
        return max(averages, key=averages.get)  # type: ignore
    
    def get_agent_stats(self) -> Dict[str, Dict]:
        """Get performance statistics for each agent."""
        stats: Dict[str, Dict] = {}
        
        for record in self._history:
            if record.agent_name and record.score is not None:
                if record.agent_name not in stats:
                    stats[record.agent_name] = {
                        "count": 0,
                        "total_score": 0.0,
                        "min_score": float('inf'),
                        "max_score": float('-inf'),
                    }
                
                s = stats[record.agent_name]
                s["count"] += 1
                s["total_score"] += record.score
                s["min_score"] = min(s["min_score"], record.score)
                s["max_score"] = max(s["max_score"], record.score)
        
        # Calculate averages
        for name, s in stats.items():
            if s["count"] > 0:
                s["avg_score"] = round(s["total_score"] / s["count"], 2)
            if s["min_score"] == float('inf'):
                s["min_score"] = None
            if s["max_score"] == float('-inf'):
                s["max_score"] = None
        
        return stats
    
    @property
    def record_count(self) -> int:
        """Number of records in memory."""
        return len(self._history)
    
    def clear(self) -> None:
        """Clear all memory."""
        self._history.clear()
        if self._persist_path and self._persist_path.exists():
            self._persist_path.unlink()
    
    def _save(self) -> None:
        """Save memory to disk."""
        if not self._persist_path:
            return
        
        data = [
            {
                "timestamp": r.timestamp,
                "event_type": r.event_type,
                "data": r.data,
                "agent_name": r.agent_name,
                "score": r.score,
                "tags": r.tags,
            }
            for r in self._history
        ]
        
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._persist_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self) -> None:
        """Load memory from disk."""
        if not self._persist_path or not self._persist_path.exists():
            return
        
        try:
            with open(self._persist_path, 'r') as f:
                data = json.load(f)
            
            self._history = [
                MemoryRecord(
                    timestamp=r["timestamp"],
                    event_type=r["event_type"],
                    data=r["data"],
                    agent_name=r.get("agent_name"),
                    score=r.get("score"),
                    tags=r.get("tags", []),
                )
                for r in data
            ]
        except Exception:
            # If loading fails, start fresh
            self._history = []


# Global singleton
_global_memory: Optional[AgentMemory] = None


def get_memory() -> AgentMemory:
    """Get the global memory instance."""
    global _global_memory
    if _global_memory is None:
        _global_memory = AgentMemory()
    return _global_memory
