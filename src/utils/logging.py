"""
Logging - Structured logging for the sales agent.
"""

import logging
import sys
from typing import Optional
from functools import lru_cache


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


@lru_cache(maxsize=10)
def get_logger(name: str = "sales_agent", level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level from parameter or default to INFO
    log_level = getattr(logging, level.upper()) if level else logging.INFO
    logger.setLevel(log_level)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Format with timestamp, level, and message
    formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_agent_run(logger: logging.Logger, agent_name: str, status: str, **kwargs):
    """
    Log an agent run with structured context.
    
    Args:
        logger: Logger instance
        agent_name: Name of the agent
        status: Run status (start, success, error)
        **kwargs: Additional context
    """
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    msg = f"Agent:{agent_name} | Status:{status}"
    if context:
        msg += f" | {context}"
    
    if status == "error":
        logger.error(msg)
    elif status == "start":
        logger.debug(msg)
    else:
        logger.info(msg)


def log_scoring(logger: logging.Logger, score: int, rule_score: int, llm_score: int, agent_name: str):
    """Log scoring results."""
    logger.info(
        f"Scoring | Agent:{agent_name} | Final:{score} | Rules:{rule_score} | LLM:{llm_score}"
    )


def log_pipeline(logger: logging.Logger, stage: str, details: str = ""):
    """Log pipeline stages."""
    msg = f"Pipeline | Stage:{stage}"
    if details:
        msg += f" | {details}"
    logger.info(msg)
