"""
Common data structures used across the project.
"""

import logging
from typing import Dict, Any, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

# Define UsageData class here
class UsageData:
    """Class representing token usage data from a model call"""

    def __init__(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: Optional[int] = None,
    ):
        self.provider = provider
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens or (prompt_tokens + completion_tokens)

        # Cost calculation will be handled by CostManager or calculate_cost function
        # These attributes will be populated after initialization
        self.prompt_cost: float = 0.0
        self.completion_cost: float = 0.0
        self.total_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert usage data to dictionary"""
        return {
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "total_cost": self.total_cost
        }

    def __repr__(self) -> str:
        return (
            f"UsageData(provider='{self.provider}', model='{self.model}', "
            f"prompt_tokens={self.prompt_tokens}, completion_tokens={self.completion_tokens}, "
            f"total_tokens={self.total_tokens}, total_cost={self.total_cost:.6f})"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, UsageData):
            return NotImplemented
        return (
            self.provider == other.provider and
            self.model == other.model and
            self.prompt_tokens == other.prompt_tokens and
            self.completion_tokens == other.completion_tokens and
            self.total_tokens == other.total_tokens and
            abs(self.prompt_cost - other.prompt_cost) < 1e-9 and # Use tolerance for float comparison
            abs(self.completion_cost - other.completion_cost) < 1e-9 and
            abs(self.total_cost - other.total_cost) < 1e-9
        )

# Note: Cost calculation logic remains in cost_manager.py
