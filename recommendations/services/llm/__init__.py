"""
Générateur de recommandations intelligent.
Méthode basée sur les LLMs (Azure OpenAI).
"""

from .generator import LLMRecommendationGenerator
from .prompts import RecommendationPrompts
from .engine import RecommendationEngine

__all__ = [
    'LLMRecommendationGenerator',
    'RecommendationPrompts',
    'RecommendationEngine'
]