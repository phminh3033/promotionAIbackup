"""Placeholder cho Agent API. Version hiện tại không gọi API và không có UI chat."""
from __future__ import annotations


class AgentEngine:
    def is_available(self) -> bool:
        return False

    def enhance(self, recommendation):
        return recommendation
