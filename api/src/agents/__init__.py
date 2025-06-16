"""
Agents module for LangGraph-based business intelligence agents.

This module provides specialized agents for sales analysis,
and other business intelligence workflows.
"""

from .base_agent import AgentConfig, AgentResult, BaseAgent, MultiStepAgent, TaskResult
from .sales_agent import SalesAnalysisAgent


__all__ = [
    # Base classes
    "BaseAgent",
    "MultiStepAgent",
    "AgentConfig",
    "AgentResult",
    "TaskResult",
    # Specialized agents
    "SalesAnalysisAgent",
]
