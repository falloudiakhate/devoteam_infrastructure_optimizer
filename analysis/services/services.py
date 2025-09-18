"""
Service principal d'analyse des anomalies.
Point d'entrée pour choisir entre les méthodes classic et LLM.
"""

import logging
from typing import Dict, Optional
from ingestion.models import InfrastructureMetrics, AnomalyDetection
from .classic.detector import ClassicAnomalyDetector
from .llm.detector import LLMAnomalyDetector

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """
    Service principal orchestrant les deux méthodes d'analyse.
    Permet de choisir entre analyse classique ou LLM selon la configuration.
    """
    
    def __init__(self, method: str = "classic"):
        """
        Initialise le service avec la méthode choisie.
        
        Args:
            method: "classic" ou "llm" pour choisir la méthode d'analyse
        """
        self.method = method
        
        if method == "classic":
            self.detector = ClassicAnomalyDetector()
        elif method == "llm":
            self.detector = LLMAnomalyDetector()
        else:
            logger.warning(f"Méthode {method} inconnue, utilisation de 'classic'")
            self.method = "classic"
            self.detector = ClassicAnomalyDetector()
    
    def analyze_metrics(self, metrics: InfrastructureMetrics) -> Optional[AnomalyDetection]:
        """
        Analyse les métriques avec la méthode configurée.
        
        Args:
            metrics: Instance des métriques à analyser
            
        Returns:
            AnomalyDetection: Instance créée ou None si erreur
        """
        logger.info(f"Analyse avec méthode {self.method} pour métrique {metrics.id}")
        return self.detector.analyze_metrics(metrics)
    
    def analyze_batch_metrics(self, metrics_queryset) -> Dict[str, int]:
        """
        Analyse un lot de métriques.
        
        Args:
            metrics_queryset: QuerySet des métriques à analyser
            
        Returns:
            Dict: Statistiques d'analyse
        """
        return self.detector.analyze_batch_metrics(metrics_queryset)
    
    @property
    def is_llm_available(self) -> bool:
        """
        Indique si la méthode LLM est disponible.
        
        Returns:
            bool: True si LLM est configuré et disponible
        """
        if self.method == "llm":
            return self.detector.is_available
        return False
    
    def get_method_info(self) -> Dict[str, any]:
        """
        Retourne les informations sur la méthode utilisée.
        
        Returns:
            Dict: Informations de configuration
        """
        info = {
            'current_method': self.method,
            'detector_class': self.detector.__class__.__name__
        }
        
        if hasattr(self.detector, 'is_available'):
            info['detector_available'] = self.detector.is_available
        
        return info