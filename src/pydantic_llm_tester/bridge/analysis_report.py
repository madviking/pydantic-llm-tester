from pydantic import BaseModel
from typing import Dict, Any, List

class PassAnalysis(BaseModel):
    """Represents the analysis for a single pass of LLM interaction."""
    new_fields: int = 0
    overwritten_fields: int = 0
    
    def __str__(self) -> str:
        """Readable string representation of the pass analysis."""
        return f"New fields: {self.new_fields}, Overwritten: {self.overwritten_fields}"

class PyllmAnalysisReport(BaseModel):
    """
    Represents the overall analysis report for a PyllmBridge ask operation.
    
    Contains detailed information about each pass and the overall results,
    including the number of fields filled, fields overwritten, and total cost.
    """
    passes: Dict[str, PassAnalysis] = {} # Key will be pass name (e.g., "first_pass")
    total_fields: int = 0
    cost: float = 0.0
    
    def get_total_new_fields(self) -> int:
        """Returns the total number of new fields filled across all passes."""
        return sum(p.new_fields for p in self.passes.values())
    
    def get_total_overwritten_fields(self) -> int:
        """Returns the total number of fields that were overwritten across all passes."""
        return sum(p.overwritten_fields for p in self.passes.values())
    
    def get_fill_percentage(self) -> float:
        """Returns the percentage of fields filled (0-100)."""
        if self.total_fields == 0:
            return 0.0
        return min(100.0, (self.get_total_new_fields() / self.total_fields) * 100)
    
    def get_pass_summary(self, pass_name: str) -> str:
        """Returns a summary of a specific pass."""
        if pass_name not in self.passes:
            return f"No data for {pass_name}"
        pass_data = self.passes[pass_name]
        return f"{pass_name}: {pass_data}"
    
    def __str__(self) -> str:
        """Readable string representation of the analysis report."""
        lines = ["Analysis Report:"]
        
        for pass_name, pass_data in self.passes.items():
            lines.append(f"  {pass_name}: {pass_data}")
        
        lines.append(f"  Total fields: {self.total_fields}")
        lines.append(f"  Fields filled: {self.get_total_new_fields()} ({self.get_fill_percentage():.1f}%)")
        lines.append(f"  Fields overwritten: {self.get_total_overwritten_fields()}")
        lines.append(f"  Total cost: ${self.cost:.6f}")
        
        return "\n".join(lines)
