"""
Moteur de génération de recommandations via LLM.
Interface spécialisée pour Azure OpenAI dans le contexte des recommandations.
"""

import logging
from typing import Dict, Any, Optional
from infrastructure_optimization.core.services import AzureOpenAIService
from ingestion.models import InfrastructureMetrics
from .prompts import RecommendationPrompts

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Moteur de génération de recommandations utilisant Azure OpenAI.
    Interface spécialisée pour les recommandations d'infrastructure.
    """
    
    def __init__(self):
        self.azure_service = AzureOpenAIService()
        self.prompts = RecommendationPrompts()
    
    def generate_recommendations(self, metrics: InfrastructureMetrics,
                               anomalies_summary: str = "") -> Optional[Dict[str, Any]]:
        """
        Génère des recommandations via Azure OpenAI.
        
        Args:
            metrics: Métriques d'infrastructure à analyser
            anomalies_summary: Résumé des anomalies détectées
            
        Returns:
            Dict: Recommandations structurées ou None si erreur
        """
        if not self.azure_service.is_available:
            logger.warning("Service Azure OpenAI non disponible pour recommandations")
            return None
        
        try:
            # Construction des messages
            messages = [
                self.azure_service.build_system_message(
                    role="expert senior en optimisation d'infrastructure IT",
                    expertise="analyse système et recommandations de performance",
                    output_format="JSON structuré"
                ),
                self.azure_service.build_user_message(
                    self.prompts.get_recommendation_prompt(metrics, anomalies_summary)
                )
            ]
            
            # Appel à Azure OpenAI avec paramètres optimisés pour recommandations
            response = self.azure_service.call_json_completion(
                messages=messages
            )
            
            if response:
                logger.info(f"Recommandations LLM générées pour métrique {metrics.id}")
                return self._validate_and_enrich_response(response, metrics)
            else:
                logger.error("Échec génération recommandations LLM")
                return None
                
        except Exception as e:
            logger.error(f"Erreur moteur recommandations LLM: {e}")
            return None
    
    def generate_focused_recommendations(self, metrics: InfrastructureMetrics,
                                       focus_area: str) -> Optional[Dict[str, Any]]:
        """
        Génère des recommandations ciblées sur un domaine spécifique.
        
        Args:
            metrics: Métriques d'infrastructure
            focus_area: Domaine à optimiser (cpu, memory, network, etc.)
            
        Returns:
            Dict: Recommandations ciblées ou None
        """
        if not self.azure_service.is_available:
            return None
        
        try:
            messages = [
                self.azure_service.build_system_message(
                    role=f"spécialiste en optimisation {focus_area}",
                    expertise=f"performance et optimisation {focus_area}",
                    output_format="JSON"
                ),
                self.azure_service.build_user_message(
                    self.prompts.get_optimization_prompt(metrics, focus_area)
                )
            ]
            
            response = self.azure_service.call_json_completion(
                messages=messages
            )
            
            if response:
                # Enrichissement avec le focus area
                response['focus_area'] = focus_area
                response['analysis_type'] = 'focused_optimization'
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur recommandations ciblées {focus_area}: {e}")
            return None
    
    def generate_capacity_planning(self, metrics: InfrastructureMetrics,
                                 projection_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Génère une analyse de planification de capacité.
        
        Args:
            metrics: Métriques actuelles
            projection_days: Horizon de projection en jours
            
        Returns:
            Dict: Analyse de capacité ou None
        """
        if not self.azure_service.is_available:
            return None
        
        try:
            messages = [
                self.azure_service.build_system_message(
                    role="expert en planification de capacité",
                    expertise="prévision de charge et dimensionnement système",
                    output_format="JSON avec projections"
                ),
                self.azure_service.build_user_message(
                    self.prompts.get_capacity_planning_prompt(metrics, projection_days)
                )
            ]
            
            response = self.azure_service.call_json_completion(
                messages=messages
            )
            
            if response:
                response['analysis_type'] = 'capacity_planning'
                response['projection_horizon_days'] = projection_days
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur planification capacité: {e}")
            return None
    
    def generate_emergency_recommendations(self, metrics: InfrastructureMetrics,
                                         critical_issue: str) -> Optional[Dict[str, Any]]:
        """
        Génère des recommandations d'urgence pour situation critique.
        
        Args:
            metrics: Métriques critiques
            critical_issue: Description du problème urgent
            
        Returns:
            Dict: Recommandations d'urgence ou None
        """
        if not self.azure_service.is_available:
            return None
        
        try:
            messages = [
                self.azure_service.build_system_message(
                    role="expert en résolution d'urgence système",
                    expertise="intervention critique et stabilisation",
                    output_format="JSON avec actions prioritaires"
                ),
                self.azure_service.build_user_message(
                    self.prompts.get_emergency_prompt(metrics, critical_issue)
                )
            ]
            
            response = self.azure_service.call_json_completion(
                messages=messages
            )
            
            if response:
                # Forçage de la priorité critique
                response['priority_level'] = 'critical'
                response['analysis_type'] = 'emergency_response'
                response['implementation_timeframe'] = 'Immédiat (< 30 min)'
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur recommandations urgence: {e}")
            return None
    
    def generate_maintenance_plan(self, metrics: InfrastructureMetrics,
                                maintenance_window: str) -> Optional[Dict[str, Any]]:
        """
        Génère un plan de maintenance optimisé.
        
        Args:
            metrics: Métriques système
            maintenance_window: Fenêtre de maintenance disponible
            
        Returns:
            Dict: Plan de maintenance ou None
        """
        if not self.azure_service.is_available:
            return None
        
        try:
            messages = [
                self.azure_service.build_system_message(
                    role="planificateur de maintenance système",
                    expertise="optimisation et planification maintenance",
                    output_format="JSON avec planning détaillé"
                ),
                self.azure_service.build_user_message(
                    self.prompts.get_maintenance_prompt(metrics, maintenance_window)
                )
            ]
            
            response = self.azure_service.call_json_completion(
                messages=messages
            )
            
            if response:
                response['analysis_type'] = 'maintenance_planning'
                response['maintenance_window'] = maintenance_window
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur plan maintenance: {e}")
            return None
    
    def _validate_and_enrich_response(self, response: Dict[str, Any],
                                    metrics: InfrastructureMetrics) -> Dict[str, Any]:
        """
        Valide et enrichit la réponse LLM avec des métadonnées.
        
        Args:
            response: Réponse brute du LLM
            metrics: Métriques analysées
            
        Returns:
            Dict: Réponse validée et enrichie
        """
        # Validation des champs obligatoires
        required_fields = [
            'executive_summary', 'detailed_analysis', 'recommendations',
            'priority_level', 'estimated_impact', 'implementation_timeframe'
        ]
        
        for field in required_fields:
            if field not in response:
                logger.warning(f"Champ manquant dans réponse LLM: {field}")
                response[field] = self._get_default_value(field)
        
        # Validation des recommandations
        if not isinstance(response['recommendations'], list):
            response['recommendations'] = []
        
        # Enrichissement avec métadonnées
        response['analysis_type'] = 'llm_recommendations'
        response['metrics_id'] = metrics.id
        response['llm_confidence'] = self._estimate_confidence(response)
        
        # Validation des priorités
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if response['priority_level'] not in valid_priorities:
            response['priority_level'] = 'medium'
        
        return response
    
    def _get_default_value(self, field: str) -> str:
        """Retourne une valeur par défaut pour un champ manquant."""
        defaults = {
            'executive_summary': 'Recommandations générées par analyse LLM.',
            'detailed_analysis': 'Analyse détaillée des métriques système.',
            'recommendations': [],
            'priority_level': 'medium',
            'estimated_impact': 'Amélioration des performances système',
            'implementation_timeframe': '1-2 semaines'
        }
        return defaults.get(field, '')
    
    def _estimate_confidence(self, response: Dict[str, Any]) -> float:
        """
        Estime la confiance dans la réponse LLM basée sur sa complétude.
        
        Args:
            response: Réponse du LLM
            
        Returns:
            float: Score de confiance (0.0 à 1.0)
        """
        confidence = 0.5  # Base
        
        # Bonus pour recommandations détaillées
        if len(response.get('recommendations', [])) >= 3:
            confidence += 0.2
        
        # Bonus pour analyse détaillée
        if len(response.get('detailed_analysis', '')) > 100:
            confidence += 0.1
        
        # Bonus pour résumé exécutif substantiel
        if len(response.get('executive_summary', '')) > 50:
            confidence += 0.1
        
        # Bonus pour timeframe spécifique
        timeframe = response.get('implementation_timeframe', '')
        if any(word in timeframe.lower() for word in ['jour', 'semaine', 'heure']):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    @property
    def is_available(self) -> bool:
        """Vérifie la disponibilité du moteur."""
        return self.azure_service.is_available