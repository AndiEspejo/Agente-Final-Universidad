"""
Base agent class for LangGraph agents with common functionality.

This module provides the foundation for all agents in the system,
including state management, error handling, and tool integration.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from uuid import uuid4

from langgraph.graph import StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel, ConfigDict, Field

from src.utils import setup_logging


logger = setup_logging(__name__)

StateT = TypeVar("StateT", bound=Dict[str, Any])


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Agent name")
    description: str = Field(description="Agent description")
    max_iterations: int = Field(default=10, description="Maximum workflow iterations")
    timeout_seconds: int = Field(default=300, description="Maximum execution time")
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts on failure"
    )
    enable_logging: bool = Field(default=True, description="Enable detailed logging")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    model_name: str = Field(default="gemini-1.5-flash", description="AI model to use")


class AgentResult(BaseModel):
    """Result from agent execution."""

    agent_name: str = Field(description="Name of the agent")
    execution_id: str = Field(description="Unique execution identifier")
    success: bool = Field(description="Whether execution was successful")
    final_state: Dict[str, Any] = Field(description="Final workflow state")
    steps_executed: int = Field(description="Number of steps executed")
    execution_time: float = Field(description="Total execution time in seconds")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    artifacts: List[Dict[str, Any]] = Field(
        default_factory=list, description="Generated artifacts"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseAgent(ABC):
    """
    Base class for all LangGraph agents.

    Provides common functionality including state management,
    error handling, and workflow orchestration.
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.name = config.name
        self.logger = setup_logging(f"agent.{self.name}")
        self.workflow: Optional[CompiledGraph] = None
        self._tools = {}
        self._setup_workflow()

    @abstractmethod
    def get_initial_state(self, **kwargs) -> StateT:
        """
        Get the initial state for the workflow.

        Args:
            **kwargs: Initial parameters

        Returns:
            Initial state instance
        """

    @abstractmethod
    def build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Configured StateGraph
        """

    def _setup_workflow(self) -> None:
        """Set up the LangGraph workflow."""
        try:
            graph = self.build_workflow()
            self.workflow = graph.compile()
            self.logger.info(f"Workflow compiled successfully for agent {self.name}")
        except Exception as e:
            self.logger.error(f"Failed to compile workflow for agent {self.name}: {e}")
            raise

    def register_tool(self, name: str, tool: Callable) -> None:
        """
        Register a tool with the agent.

        Args:
            name: Tool name
            tool: Tool function
        """
        self._tools[name] = tool
        self.logger.debug(f"Registered tool '{name}' with agent {self.name}")

    def get_tool(self, name: str) -> Optional[Callable]:
        """
        Get a registered tool.

        Args:
            name: Tool name

        Returns:
            Tool function or None if not found
        """
        return self._tools.get(name)

    async def execute(self, **kwargs) -> AgentResult:
        """
        Execute the agent workflow.

        Args:
            **kwargs: Initial parameters for the workflow

        Returns:
            Agent execution result
        """
        execution_id = str(uuid4())
        start_time = datetime.now()

        self.logger.info(f"Starting execution {execution_id} for agent {self.name}")

        try:
            # Get initial state
            initial_state = self.get_initial_state(**kwargs)

            if self.config.enable_logging:
                self.logger.info(f"Initial state: {initial_state.model_dump()}")

            # Execute workflow
            if not self.workflow:
                raise RuntimeError("Workflow not compiled")

            final_state = await self.workflow.ainvoke(initial_state.model_dump())

            execution_time = (datetime.now() - start_time).total_seconds()

            result = AgentResult(
                agent_name=self.name,
                execution_id=execution_id,
                success=final_state.get("status") == "completed",
                final_state=final_state,
                steps_executed=final_state.get("step", 0),
                execution_time=execution_time,
                artifacts=final_state.get("artifacts", []),
                metadata={
                    "config": self.config.model_dump(),
                    "tools_used": final_state.get("tools_used", []),
                    "ai_interactions": final_state.get("ai_interactions", 0),
                },
            )

            self.logger.info(
                f"Execution {execution_id} completed successfully in {execution_time:.2f}s"
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            self.logger.error(f"Execution {execution_id} failed: {error_msg}")

            return AgentResult(
                agent_name=self.name,
                execution_id=execution_id,
                success=False,
                final_state=kwargs,
                steps_executed=0,
                execution_time=execution_time,
                error_message=error_msg,
                metadata={"config": self.config.model_dump()},
            )

    def execute_sync(self, **kwargs) -> AgentResult:
        """
        Synchronous version of execute.

        Args:
            **kwargs: Initial parameters for the workflow

        Returns:
            Agent execution result
        """
        import asyncio

        return asyncio.run(self.execute(**kwargs))

    def validate_input(self, **kwargs) -> None:
        """
        Validate input parameters.

        Args:
            **kwargs: Input parameters to validate

        Raises:
            ValueError: If validation fails
        """
        # Override in subclasses for specific validation

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Status information
        """
        return {
            "name": self.name,
            "description": self.config.description,
            "tools_count": len(self._tools),
            "workflow_compiled": self.workflow is not None,
            "config": self.config.model_dump(),
        }


class MultiStepAgent(BaseAgent):
    """
    Base class for agents that execute multiple sequential steps.

    Provides common patterns for step-based workflows with
    conditional execution and error recovery.
    """

    def __init__(self, config: AgentConfig):
        """Initialize the multi-step agent."""
        super().__init__(config)
        self._step_handlers: Dict[str, Callable] = {}

    def register_step(self, step_name: str, handler: Callable) -> None:
        """
        Register a step handler.

        Args:
            step_name: Name of the step
            handler: Step handler function
        """
        self._step_handlers[step_name] = handler
        self.logger.debug(f"Registered step '{step_name}' with agent {self.name}")

    def get_step_handler(self, step_name: str) -> Optional[Callable]:
        """
        Get a step handler.

        Args:
            step_name: Name of the step

        Returns:
            Step handler function or None if not found
        """
        return self._step_handlers.get(step_name)

    def should_continue(self, state: Dict[str, Any]) -> bool:
        """
        Determine if workflow should continue.

        Args:
            state: Current workflow state

        Returns:
            Whether to continue execution
        """
        status = state.get("status", "running")
        step = state.get("step", 0)
        max_iterations = self.config.max_iterations

        return (
            status in ["running", "processing"]
            and step < max_iterations
            and not state.get("error")
        )

    def handle_error(self, state: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """
        Handle workflow errors.

        Args:
            state: Current workflow state
            error: The error that occurred

        Returns:
            Updated state with error handling
        """
        retry_count = state.get("retry_count", 0)

        if retry_count < self.config.retry_attempts:
            state["retry_count"] = retry_count + 1
            state["last_error"] = str(error)
            state["status"] = "retrying"
            self.logger.warning(
                f"Retrying step {state.get('step', 0)} (attempt {retry_count + 1})"
            )
        else:
            state["status"] = "failed"
            state["error"] = str(error)
            state["error_step"] = state.get("step", 0)
            self.logger.error(f"Agent failed after {retry_count} retries: {error}")

        return state


class TaskResult(BaseModel):
    """Result from a specific task execution."""

    task_name: str = Field(description="Name of the task")
    success: bool = Field(description="Whether task was successful")
    data: Any = Field(description="Task result data")
    execution_time: float = Field(description="Task execution time")
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")


def create_agent_factory() -> Dict[str, Type[BaseAgent]]:
    """
    Create a factory for agent creation.

    Returns:
        Dictionary mapping agent names to classes
    """
    return {"base": BaseAgent, "multi_step": MultiStepAgent}


def validate_agent_config(config: AgentConfig) -> None:
    """
    Validate agent configuration.

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if config.max_iterations <= 0:
        raise ValueError("max_iterations must be positive")

    if config.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    if config.retry_attempts < 0:
        raise ValueError("retry_attempts cannot be negative")

    if not config.name:
        raise ValueError("Agent name is required")
