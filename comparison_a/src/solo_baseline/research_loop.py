"""Sequential loop lives in SoloResearchAgent.run; no worker or agent pool exists."""
from .agent import SoloResearchAgent

__all__ = ["SoloResearchAgent"]
