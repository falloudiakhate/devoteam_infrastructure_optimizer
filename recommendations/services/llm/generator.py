"""
Générateur de recommandations intelligent basé sur les LLMs.
Interface principale pour la génération via Azure OpenAI.
"""

import logging
from typing import Dict, Optional
from django.utils import timezone
from ingestion.models import InfrastructureMetrics
from recommendations.models import RecommendationReport
from .engine import RecommendationEngine

logger = logging.getLogger(__name__)


class LLMRecommendationGenerator:
    """
    Générateur de recommandations intelligent utilisant Azure OpenAI.
    Analyse contextuelle avancée pour des recommandations personnalisées.
    """
    
    def __init__(self):
        self.engine = RecommendationEngine()
    
    def generate_recommendations(self, metrics: InfrastructureMetrics,
                               anomalies_summary: str = "") -> Dict:
        """
        Génère des recommandations via analyse LLM intelligente.
        
        Args:
            metrics: Métriques d'infrastructure à analyser
            anomalies_summary: Résumé des anomalies détectées
            
        Returns:
            Dict: Recommandations structurées
        """
        logger.info(f"Génération recommandations LLM pour métrique {metrics.id}")
        
        if not self.engine.is_available:
            logger.warning("Moteur LLM indisponible, utilisation du fallback")
            return self._get_fallback_recommendations(metrics, anomalies_summary)
        
        try:
            # Génération principale via LLM
            recommendations = self.engine.generate_recommendations(metrics, anomalies_summary)
            
            if recommendations:
                # Enrichissement avec analyses complémentaires si nécessaire
                recommendations = self._enrich_recommendations(recommendations, metrics)
                return recommendations
            else:
                logger.warning("Échec génération LLM, utilisation fallback")
                return self._get_fallback_recommendations(metrics, anomalies_summary)
                
        except Exception as e:
            logger.error(f"Erreur génération recommandations LLM: {e}")
            return self._get_fallback_recommendations(metrics, anomalies_summary)
    
    def generate_focused_recommendations(self, metrics: InfrastructureMetrics,
                                       focus_area: str) -> Dict:
        """
        Génère des recommandations ciblées sur un domaine spécifique.
        
        Args:
            metrics: Métriques d'infrastructure
            focus_area: Domaine à optimiser (cpu, memory, network, storage, services)
            
        Returns:
            Dict: Recommandations ciblées
        """
        logger.info(f"Génération recommandations ciblées {focus_area} pour métrique {metrics.id}")
        
        if not self.engine.is_available:
            return self._get_focused_fallback(metrics, focus_area)
        
        try:
            recommendations = self.engine.generate_focused_recommendations(metrics, focus_area)
            
            if recommendations:
                return recommendations
            else:
                return self._get_focused_fallback(metrics, focus_area)
                
        except Exception as e:
            logger.error(f"Erreur recommandations ciblées {focus_area}: {e}")
            return self._get_focused_fallback(metrics, focus_area)
    
    def generate_capacity_analysis(self, metrics: InfrastructureMetrics,
                                 projection_days: int = 30) -> Dict:
        """
        Génère une analyse de planification de capacité.
        
        Args:
            metrics: Métriques actuelles
            projection_days: Horizon de projection
            
        Returns:
            Dict: Analyse de capacité
        """
        logger.info(f"Génération analyse capacité pour métrique {metrics.id}")
        
        if not self.engine.is_available:
            return self._get_capacity_fallback(metrics, projection_days)
        
        try:
            analysis = self.engine.generate_capacity_planning(metrics, projection_days)
            
            if analysis:
                return analysis
            else:
                return self._get_capacity_fallback(metrics, projection_days)
                
        except Exception as e:
            logger.error(f"Erreur analyse capacité: {e}")
            return self._get_capacity_fallback(metrics, projection_days)
    
    def generate_emergency_response(self, metrics: InfrastructureMetrics,
                                  critical_issue: str) -> Dict:
        """
        Génère des recommandations d'urgence pour situation critique.
        
        Args:
            metrics: Métriques critiques
            critical_issue: Description du problème urgent
            
        Returns:
            Dict: Recommandations d'urgence
        """
        logger.warning(f"Génération recommandations urgence: {critical_issue}")
        
        if not self.engine.is_available:
            return self._get_emergency_fallback(metrics, critical_issue)
        
        try:
            recommendations = self.engine.generate_emergency_recommendations(metrics, critical_issue)
            
            if recommendations:
                return recommendations
            else:
                return self._get_emergency_fallback(metrics, critical_issue)
                
        except Exception as e:
            logger.error(f"Erreur recommandations urgence: {e}")
            return self._get_emergency_fallback(metrics, critical_issue)
    
    def _enrich_recommendations(self, recommendations: Dict, 
                              metrics: InfrastructureMetrics) -> Dict:
        """
        Enrichit les recommandations avec des analyses complémentaires.
        
        Args:
            recommendations: Recommandations de base
            metrics: Métriques analysées
            
        Returns:
            Dict: Recommandations enrichies
        """
        # Détection automatique de domaines critiques pour analyses ciblées
        critical_areas = self._detect_critical_areas(metrics)
        
        if critical_areas and self.engine.is_available:
            try:
                # Ajout d'une analyse ciblée pour le domaine le plus critique
                primary_area = critical_areas[0]
                focused_analysis = self.engine.generate_focused_recommendations(metrics, primary_area)
                
                if focused_analysis and 'recommendations' in focused_analysis:
                    # Fusion des recommandations
                    base_recommendations = recommendations.get('recommendations', [])
                    focused_recommendations = focused_analysis.get('recommendations', [])
                    
                    # Ajout des recommandations ciblées avec marquage spécial
                    for rec in focused_recommendations[:2]:  # Limite à 2 recommandations ciblées
                        rec['source'] = f'focused_{primary_area}'
                        base_recommendations.append(rec)
                    
                    recommendations['recommendations'] = base_recommendations
                    
                    # Enrichissement du résumé
                    if 'detailed_analysis' in recommendations:
                        recommendations['detailed_analysis'] += f" Analyse ciblée {primary_area} incluse."
                        
            except Exception as e:
                logger.warning(f"Erreur enrichissement recommandations: {e}")
        
        return recommendations
    
    def _detect_critical_areas(self, metrics: InfrastructureMetrics) -> list:
        """
        Détecte les domaines critiques nécessitant une attention particulière.
        
        Args:
            metrics: Métriques à analyser
            
        Returns:
            list: Liste des domaines critiques ordonnés par priorité
        """
        critical_areas = []
        
        # Détection CPU critique
        if metrics.cpu_usage > 85:
            critical_areas.append('cpu')
        
        # Détection mémoire critique  
        if metrics.memory_usage > 85:
            critical_areas.append('memory')
        
        # Détection stockage critique
        if metrics.disk_usage > 85:
            critical_areas.append('storage')
        
        # Détection réseau/latence critique
        if metrics.latency_ms > 500:
            critical_areas.append('network')
        
        # Détection services dégradés
        if metrics.has_degraded_services:
            critical_areas.append('services')
        
        return critical_areas
    
    def _get_fallback_recommendations(self, metrics: InfrastructureMetrics,
                                    anomalies_summary: str) -> Dict:
        """
        Recommandations de fallback quand LLM n'est pas disponible.
        
        Args:
            metrics: Métriques à analyser
            anomalies_summary: Résumé des anomalies
            
        Returns:
            Dict: Recommandations de base
        """
        from ..classic import ClassicRecommendationGenerator
        
        classic_generator = ClassicRecommendationGenerator()
        recommendations = classic_generator.generate_recommendations(metrics, anomalies_summary)
        
        # Marquage comme fallback
        recommendations['analysis_type'] = 'llm_fallback'
        recommendations['detailed_analysis'] += " (Analyse LLM temporairement indisponible)"
        
        return recommendations
    
    def _get_focused_fallback(self, metrics: InfrastructureMetrics, focus_area: str) -> Dict:
        """Fallback pour recommandations ciblées."""
        return {
            'executive_summary': f'Analyse {focus_area} via méthode classique (LLM indisponible)',
            'detailed_analysis': f'Recommandations de base pour {focus_area}',
            'recommendations': [
                {
                    'title': f'Surveillance {focus_area}',
                    'description': f'Monitoring renforcé des métriques {focus_area}',
                    'priority': 'medium',
                    'category': focus_area
                }
            ],
            'priority_level': 'medium',
            'estimated_impact': 'Impact modéré',
            'implementation_timeframe': '1 semaine',
            'focus_area': focus_area,
            'analysis_type': 'focused_fallback'
        }
    
    def _get_capacity_fallback(self, metrics: InfrastructureMetrics, days: int) -> Dict:
        """Fallback pour analyse de capacité."""
        return {
            'executive_summary': f'Analyse capacité {days} jours (méthode classique)',
            'detailed_analysis': 'Projection basée sur les métriques actuelles',
            'recommendations': [
                {
                    'title': 'Surveillance capacité',
                    'description': f'Monitoring des ressources pour projection {days} jours',
                    'priority': 'medium',
                    'category': 'monitoring'
                }
            ],
            'priority_level': 'medium',
            'estimated_impact': 'Prévention saturation ressources',
            'implementation_timeframe': f'{days} jours',
            'analysis_type': 'capacity_fallback',
            'projection_horizon_days': days
        }
    
    def _get_emergency_fallback(self, metrics: InfrastructureMetrics, issue: str) -> Dict:
        """Fallback pour recommandations d'urgence."""
        return {
            'executive_summary': f'Réponse urgence: {issue}',
            'detailed_analysis': 'Recommandations d\'urgence basées sur les métriques critiques',
            'recommendations': [
                {
                    'title': 'Investigation immédiate',
                    'description': f'Investiguer et résoudre: {issue}',
                    'priority': 'critical',
                    'category': 'emergency'
                },
                {
                    'title': 'Surveillance renforcée',
                    'description': 'Monitoring continu des métriques critiques',
                    'priority': 'high',
                    'category': 'monitoring'
                }
            ],
            'priority_level': 'critical',
            'estimated_impact': 'Stabilisation système',
            'implementation_timeframe': 'Immédiat',
            'analysis_type': 'emergency_fallback'
        }
    
    def generate_report(self, metrics: InfrastructureMetrics) -> Optional[RecommendationReport]:
        """
        Génère un rapport complet avec la méthode LLM.
        
        Args:
            metrics: Métriques à analyser
            
        Returns:
            RecommendationReport: Rapport généré ou None
        """
        try:
            # Récupération du résumé des anomalies
            anomalies_summary = "Aucune anomalie détectée"
            if hasattr(metrics, 'anomaly_detection') and metrics.anomaly_detection:
                anomalies_summary = metrics.anomaly_detection.anomaly_summary
            
            # Génération des recommandations
            recommendations_data = self.generate_recommendations(metrics, anomalies_summary)
            
            # Création ou mise à jour du rapport
            report, created = RecommendationReport.objects.update_or_create(
                metrics=metrics,
                defaults={
                    'executive_summary': recommendations_data['executive_summary'],
                    'detailed_analysis': recommendations_data['detailed_analysis'],
                    'recommendations_json': {'actions': recommendations_data['recommendations']},
                    'priority_level': recommendations_data['priority_level'],
                    'estimated_impact': recommendations_data['estimated_impact'],
                    'implementation_timeframe': recommendations_data['implementation_timeframe'],
                    'generation_method': 'llm',
                    'generated_at': timezone.now()
                }
            )
            
            action = "créé" if created else "mis à jour"
            logger.info(f"Rapport LLM {action}: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Erreur génération rapport LLM: {e}")
            return None
    
    @property
    def is_available(self) -> bool:
        """Vérifie la disponibilité du générateur."""
        return self.engine.is_available