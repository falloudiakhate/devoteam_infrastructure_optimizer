"""
Prompts spécialisés pour la génération de recommandations via LLM.
Templates optimisés pour Azure OpenAI dans le contexte des recommandations.
"""

import json
from typing import Dict, Any, List
from ingestion.models import InfrastructureMetrics


class RecommendationPrompts:
    """
    Collection de prompts spécialisés pour la génération de recommandations.
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        Prompt système pour l'assistant spécialisé en recommandations infrastructure.
        
        Returns:
            str: Prompt système optimisé
        """
        return """Vous êtes un expert senior en optimisation d'infrastructure IT pour entreprise.

VOTRE MISSION :
Analyser les métriques système et fournir des recommandations concrètes, actionnables et priorisées pour optimiser les performances et la fiabilité de l'infrastructure.

EXPERTISE :
- Architecture système et optimisation de performance  
- Gestion des ressources (CPU, mémoire, stockage, réseau)
- Résolution de problèmes de production
- Planification de capacité et scalabilité
- Bonnes pratiques DevOps et monitoring

STYLE DE RÉPONSE :
- Professionnel et technique mais accessible
- Recommandations concrètes avec justifications
- Priorisation claire des actions
- Estimation des impacts et délais réalistes

FORMAT DE RÉPONSE :
Répondez UNIQUEMENT en JSON avec cette structure exacte :
{
  "executive_summary": "résumé_exécutif_2_3_phrases",
  "detailed_analysis": "analyse_détaillée_de_la_situation",
  "recommendations": [
    {
      "title": "titre_de_la_recommandation",
      "description": "description_détaillée_de_l_action",
      "priority": "low|medium|high|critical",
      "category": "performance|resources|network|storage|services|security|monitoring"
    }
  ],
  "priority_level": "priorité_globale_low_medium_high_critical",
  "estimated_impact": "description_impact_attendu",
  "implementation_timeframe": "délai_estimation_réaliste"
}"""
    
    @staticmethod
    def get_recommendation_prompt(metrics: InfrastructureMetrics, 
                                anomalies_summary: str) -> str:
        """
        Génère le prompt de recommandations avec contexte métrique.
        
        Args:
            metrics: Métriques d'infrastructure
            anomalies_summary: Résumé des anomalies détectées
            
        Returns:
            str: Prompt contextualisé pour les recommandations
        """
        return f"""Analysez ces métriques d'infrastructure et générez des recommandations d'optimisation spécifiques :

MÉTRIQUES SYSTÈME ACTUELLES :
- CPU: {metrics.cpu_usage}% (seuil attention: >80%, critique: >95%)
- Mémoire: {metrics.memory_usage}% (seuil attention: >85%, critique: >95%)
- Latence: {metrics.latency_ms}ms (seuil attention: >300ms, critique: >1000ms)
- Disque: {metrics.disk_usage}% (seuil attention: >85%, critique: >95%)
- I/O Wait: {metrics.io_wait}% (seuil attention: >20%)
- Threads: {metrics.thread_count} threads actifs
- Connexions: {metrics.active_connections} connexions actives
- Taux d'erreur: {metrics.error_rate*100:.2f}% (seuil attention: >1%, critique: >5%)
- Température: {metrics.temperature_celsius}°C (seuil attention: >70°C, critique: >80°C)
- Consommation: {metrics.power_consumption_watts}W
- Uptime: {metrics.uptime_hours}h

STATUT DES SERVICES :
{json.dumps(metrics.service_status, indent=2, ensure_ascii=False)}

ANOMALIES DÉTECTÉES :
{anomalies_summary}

CONTEXTE OPÉRATIONNEL :
- Infrastructure de production critique
- Besoin de haute disponibilité (99.9%+)
- Budget d'optimisation disponible
- Équipe technique expérimentée
- Fenêtres de maintenance limitées

OBJECTIFS PRIORITAIRES :
1. Garantir la stabilité et performance
2. Prévenir les pannes et dégradations
3. Optimiser l'utilisation des ressources
4. Améliorer la surveillance et l'observabilité
5. Planifier la montée en charge

Fournissez des recommandations spécifiques, priorisées et actionnables pour cette infrastructure."""
    
    @staticmethod
    def get_optimization_prompt(metrics: InfrastructureMetrics,
                              focus_area: str) -> str:
        """
        Prompt spécialisé pour l'optimisation d'un domaine particulier.
        
        Args:
            metrics: Métriques d'infrastructure
            focus_area: Domaine à optimiser (cpu, memory, network, etc.)
            
        Returns:
            str: Prompt spécialisé
        """
        focus_descriptions = {
            'cpu': 'optimisation des performances CPU et processeur',
            'memory': 'gestion et optimisation de la mémoire système',
            'network': 'optimisation réseau et réduction de la latence',
            'storage': 'gestion du stockage et des I/O disque',
            'services': 'stabilisation et optimisation des services'
        }
        
        focus_desc = focus_descriptions.get(focus_area, 'optimisation générale')
        
        return f"""Expert en {focus_desc}, analysez ces métriques et fournissez des recommandations ciblées :

                FOCUS D'ANALYSE : {focus_area.upper()}

                MÉTRIQUES PERTINENTES :
                - CPU: {metrics.cpu_usage}%
                - Mémoire: {metrics.memory_usage}%
                - Latence: {metrics.latency_ms}ms
                - I/O Wait: {metrics.io_wait}%
                - Services: {len([s for s, status in metrics.service_status.items() if status != 'healthy'])} services non-optimaux

                DEMANDE SPÉCIFIQUE :
                Concentrez-vous exclusivement sur {focus_desc}. Fournissez 3-5 recommandations très spécifiques et techniques pour ce domaine uniquement.

                Ignorez les autres aspects système et détaillez précisément :
                1. Le problème identifié dans ce domaine
                2. La solution technique recommandée  
                3. Les étapes d'implémentation concrètes
                4. Les métriques à surveiller pour valider l'amélioration

                Répondez au format JSON standard."""
    
    @staticmethod
    def get_capacity_planning_prompt(metrics: InfrastructureMetrics,
                                   projection_days: int = 30) -> str:
        """
        Prompt pour la planification de capacité.
        
        Args:
            metrics: Métriques actuelles
            projection_days: Nombre de jours de projection
            
        Returns:
            str: Prompt de planification de capacité
        """
        return f"""Expert en planification de capacité, analysez ces métriques pour anticiper les besoins futurs :

MÉTRIQUES ACTUELLES DE BASE :
- CPU: {metrics.cpu_usage}%
- Mémoire: {metrics.memory_usage}%
- Disque: {metrics.disk_usage}%
- Connexions: {metrics.active_connections}
- Uptime: {metrics.uptime_hours}h

HORIZON DE PROJECTION : {projection_days} jours

MISSION :
1. Identifiez les ressources approchant de la saturation
2. Estimez la croissance attendue basée sur les métriques
3. Prédisez les points de rupture potentiels
4. Recommandez les actions préventives de scaling

LIVRABLES ATTENDUS :
- Analyse de tendance pour chaque ressource critique
- Prévisions de saturation (dates approximatives)
- Recommandations de dimensionnement
- Planning d'actions préventives

Format JSON avec section 'capacity_analysis' détaillant les projections."""
    
    @staticmethod
    def get_emergency_prompt(metrics: InfrastructureMetrics,
                           critical_issue: str) -> str:
        """
        Prompt d'urgence pour situations critiques.
        
        Args:
            metrics: Métriques critiques
            critical_issue: Description du problème critique
            
        Returns:
            str: Prompt d'urgence
        """
        return f"""SITUATION D'URGENCE - INTERVENTION IMMÉDIATE REQUISE

PROBLÈME CRITIQUE IDENTIFIÉ :
{critical_issue}

MÉTRIQUES CRITIQUES :
- CPU: {metrics.cpu_usage}%
- Mémoire: {metrics.memory_usage}%  
- Disque: {metrics.disk_usage}%
- Erreurs: {metrics.error_rate*100:.2f}%
- Services dégradés: {metrics.has_degraded_services}

CONTRAINTES D'URGENCE :
- Système en production avec utilisateurs actifs
- Risque d'indisponibilité service  
- Intervention rapide nécessaire (< 30 minutes)
- Éviter l'arrêt complet si possible

DEMANDE PRIORITAIRE :
1. Actions IMMÉDIATES (< 5 min) pour stabiliser
2. Actions URGENTES (< 30 min) pour résoudre  
3. Actions de SUIVI pour éviter récurrence
4. Points de surveillance critique

IMPORTANT : Priorisez la stabilisation sur l'optimisation.

Format JSON avec priorité 'critical' et timeframe 'immédiat'."""
    
    @staticmethod
    def get_maintenance_prompt(metrics: InfrastructureMetrics,
                             maintenance_window: str) -> str:
        """
        Prompt pour recommandations de maintenance programmée.
        
        Args:
            metrics: Métriques système
            maintenance_window: Fenêtre de maintenance disponible
            
        Returns:
            str: Prompt de maintenance
        """
        return f"""Planification de maintenance programmée - Optimisations système

FENÊTRE DE MAINTENANCE DISPONIBLE :
{maintenance_window}

ÉTAT SYSTÈME ACTUEL :
- CPU: {metrics.cpu_usage}%
- Mémoire: {metrics.memory_usage}%
- Uptime: {metrics.uptime_hours}h
- Services actifs: {len(metrics.service_status)} services

OBJECTIFS DE MAINTENANCE :
1. Optimisations nécessitant redémarrage/arrêt
2. Mises à jour et patches système
3. Nettoyage et consolidation de données
4. Tests de performance et stress
5. Validation des sauvegardes

CONTRAINTES :
- Durée limitée de la fenêtre de maintenance
- Procédures de rollback nécessaires
- Tests de validation post-maintenance
- Communication utilisateurs requise

Priorisez les actions par impact/durée et fournissez un planning détaillé d'exécution.

Format JSON avec section 'maintenance_plan' incluant timeline et checkpoints."""