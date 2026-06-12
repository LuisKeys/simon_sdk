"""Agent event types for the hooks system."""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentEvent:
    """An observable event emitted during an agent run.

    ``type`` is one of:
    - ``"model_selected"`` — the provider/model was resolved
    - ``"tool_called"`` — a tool finished executing (ReAct loop)
    - ``"retry_attempted"`` — a with_retry call is about to retry
    - ``"response_received"`` — the final response is ready

    ``data`` carries event-specific key/value pairs.
    """

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
