"""
Services de génération de recommandations.

Structure avec 2 approches distinctes :
- classic/ : Méthode basée sur des règles prédéfinies
- llm/ : Méthode intelligente basée sur les LLMs
"""

from .services import RecommendationService
from .classic.generator import ClassicRecommendationGenerator
from .llm.generator import LLMRecommendationGenerator

__all__ = [
    'RecommendationService',
    'ClassicRecommendationGenerator',
    'LLMRecommendationGenerator'
]