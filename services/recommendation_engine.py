"""Recommendation chạy hoàn toàn bằng mô hình hiện có. Không gọi Agent khi chưa khả dụng."""
from __future__ import annotations

from services.agent_engine import AgentEngine
from services.scientific_model_engine import ScientificModelEngine
from src.recommendation.engine import build_recommendation_card


class RecommendationEngine:
    def __init__(self) -> None:
        self.scientific = ScientificModelEngine()
        self.agent = AgentEngine()

    def build_card(self, **kwargs):
        card = build_recommendation_card(**kwargs)
        if self.agent.is_available():
            return self.agent.enhance(card)
        return card
