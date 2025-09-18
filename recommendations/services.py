"""
Service principal de génération de recommandations.
Point d'entrée pour choisir entre les méthodes classic et LLM.
"""

import logging
from typing import Dict, Optional
from ingestion.models import InfrastructureMetrics
from recommendations.models import RecommendationReport
from .services.classic import ClassicRecommendationGenerator
from .services.llm import LLMRecommendationGenerator

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Service principal orchestrant les deux méthodes de génération de recommandations.
    Permet de choisir entre génération classique ou LLM selon la configuration.
    """
    
    def __init__(self, method: str = "classic"):
        """
        Initialise le service avec la méthode choisie.
        
        Args:
            method: "classic" ou "llm" pour choisir la méthode de génération
        """
        self.method = method
        
        if method == "classic":
            self.generator = ClassicRecommendationGenerator()
        elif method == "llm":
            self.generator = LLMRecommendationGenerator()
        else:
            logger.warning(f"Méthode {method} inconnue, utilisation de 'classic'")
            self.method = "classic"
            self.generator = ClassicRecommendationGenerator()
    
    def generate_recommendation_report(self, metrics: InfrastructureMetrics) -> Optional[RecommendationReport]:
        """
        Génère un rapport de recommandations avec la méthode configurée.
        
        Args:
            metrics: Instance des métriques à analyser
            
        Returns:
            RecommendationReport: Rapport généré ou None si erreur
        """
        logger.info(f"Génération rapport recommandations {self.method} pour métrique {metrics.id}")
        return self.generator.generate_report(metrics)
    
    def generate_batch_reports(self, metrics_queryset) -> Dict[str, int]:
        """
        Génère des rapports pour un lot de métriques.
        
        Args:
            metrics_queryset: QuerySet des métriques à traiter
            
        Returns:
            Dict: Statistiques de génération
        """
        results = {
            'total': metrics_queryset.count(),
            'generated': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for metrics in metrics_queryset:
            try:
                report = self.generate_recommendation_report(metrics)
                if report:
                    results['generated'] += 1
                else:
                    results['errors'] += 1
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Erreur génération rapport lot métrique {metrics.id}: {e}")
        
        logger.info(f"Génération lot rapports {self.method} terminée: "
                   f"{results['generated']}/{results['total']} succès")
        
        return results
    
    @property
    def is_llm_available(self) -> bool:
        """
        Indique si la méthode LLM est disponible.
        
        Returns:
            bool: True si LLM est configuré et disponible
        """
        if self.method == "llm":
            return self.generator.is_available
        return False
    
    def get_method_info(self) -> Dict[str, any]:
        """
        Retourne les informations sur la méthode utilisée.
        
        Returns:
            Dict: Informations de configuration
        """
        info = {
            'current_method': self.method,
            'generator_class': self.generator.__class__.__name__
        }
        
        if hasattr(self.generator, 'is_available'):
            info['generator_available'] = self.generator.is_available
        
        return info