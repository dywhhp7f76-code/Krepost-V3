"""
krepost.orchestration — слой маршрутизации и оркестрации между
безопасностью и моделями (ARCHITECTURE_VISION §4, §5.3).
"""
from krepost.orchestration.backends import (
    CallableBackend,
    EchoBackend,
    ModelBackend,
)
from krepost.orchestration.orchestrator import (
    Orchestrator,
    OrchestrationResult,
    OrchestrationStatus,
)
from krepost.orchestration.router import Route, Router
from krepost.orchestration.tools import (
    AgentResult,
    FinalAnswer,
    Tool,
    ToolAgent,
    ToolCall,
    ToolCallingBackend,
    ToolRegistry,
    ToolTraceEntry,
    make_fetch_tool,
)

__all__ = [
    "ModelBackend",
    "CallableBackend",
    "EchoBackend",
    "Route",
    "Router",
    "Orchestrator",
    "OrchestrationResult",
    "OrchestrationStatus",
    # tool-loop
    "ToolAgent",
    "ToolCall",
    "FinalAnswer",
    "Tool",
    "ToolRegistry",
    "ToolCallingBackend",
    "make_fetch_tool",
    "AgentResult",
    "ToolTraceEntry",
]
