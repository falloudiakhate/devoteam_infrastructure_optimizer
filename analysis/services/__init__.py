"""
Package services pour l'analyse des anomalies.

Structure séparée avec 2 approches distinctes :
- classic/ : Méthode classique basée sur des seuils
- llm/ : Méthode intelligente basée sur les LLMs
"""

from .services import AnomalyDetectionService
from .classic.detector import ClassicAnomalyDetector
from .llm.detector import LLMAnomalyDetector

__all__ = [
    'AnomalyDetectionService',
    'ClassicAnomalyDetector',
    'LLMAnomalyDetector'
]