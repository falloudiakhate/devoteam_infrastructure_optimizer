"""
Filtres pour l'application de recommandations.
Centralise la logique de filtrage pour les rapports de recommandations.
"""

from typing import Dict, Any
from django.db.models import QuerySet
from django.utils import timezone
from datetime import timedelta

from recommendations.models import RecommendationReport
from ingestion.models import InfrastructureMetrics


class RecommendationFilters:
    """
    Filtres pour les rapports de recommandations.
    """
    
    @staticmethod
    def get_filtered_reports(query_params: Dict[str, Any]) -> QuerySet:
        """
        Applique les filtres sur les rapports de recommandations.
        
        Args:
            query_params: Paramètres de requête GET
            
        Returns:
            QuerySet: Rapports filtrés
        """
        queryset = RecommendationReport.objects.select_related('metrics').order_by('-generated_at')
        
        # Filtre par priorité
        priority = query_params.get('priority')
        if priority and priority in ['low', 'medium', 'high', 'critical']:
            queryset = queryset.filter(priority_level=priority)
        
        # Filtre rapports urgents uniquement
        urgent_only = query_params.get('urgent_only')
        if urgent_only and urgent_only.lower() in ['true', '1', 'yes']:
            queryset = queryset.filter(priority_level__in=['high', 'critical'])
        
        # Filtre par méthode de génération
        method = query_params.get('method')
        if method and method in ['classic', 'llm']:
            queryset = queryset.filter(generation_method=method)
        
        # Filtre par période
        days = query_params.get('last_days')
        if days:
            try:
                days_int = int(days)
                date_limit = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(generated_at__gte=date_limit)
            except ValueError:
                pass  # Ignorer si pas un entier valide
        
        # Limite du nombre de résultats
        limit = query_params.get('limit', '50')
        try:
            limit_int = int(limit)
            queryset = queryset[:limit_int]
        except ValueError:
            queryset = queryset[:50]  # Limite par défaut
        
        return queryset
    
    @staticmethod
    def get_filter_info(query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retourne les informations sur les filtres appliqués.
        
        Args:
            query_params: Paramètres de requête GET
            
        Returns:
            Dict: Informations sur les filtres
        """
        filters_applied = {}
        
        if query_params.get('priority'):
            filters_applied['priority'] = query_params.get('priority')
        
        if query_params.get('urgent_only'):
            filters_applied['urgent_only'] = query_params.get('urgent_only').lower() == 'true'
        
        if query_params.get('method'):
            filters_applied['method'] = query_params.get('method')
        
        if query_params.get('last_days'):
            try:
                filters_applied['last_days'] = int(query_params.get('last_days'))
            except ValueError:
                pass
        
        filters_applied['limit'] = int(query_params.get('limit', '50'))
        
        return filters_applied


class MetricsFilters:
    """
    Filtres pour les métriques dans le contexte des recommandations.
    """
    
    @staticmethod
    def get_metrics_without_reports() -> QuerySet:
        """
        Récupère les métriques analysées sans rapport de recommandations.
        
        Returns:
            QuerySet: Métriques analysées sans rapport
        """
        return InfrastructureMetrics.objects.filter(
            analysis_completed=True,
            recommendation_report__isnull=True
        ).order_by('-timestamp')
    
    @staticmethod
    def get_metrics_with_critical_anomalies() -> QuerySet:
        """
        Récupère les métriques avec des anomalies critiques nécessitant des recommandations.
        
        Returns:
            QuerySet: Métriques avec anomalies critiques
        """
        return InfrastructureMetrics.objects.filter(
            analysis_completed=True,
            is_anomalous=True,
            anomaly_detection__severity_score__gte=7
        ).order_by('-timestamp')
    
    @staticmethod
    def validate_metrics_id(metrics_id: str) -> int:
        """
        Valide et convertit un ID de métrique.
        
        Args:
            metrics_id: ID à valider
            
        Returns:
            int: ID validé
            
        Raises:
            ValueError: Si l'ID n'est pas valide
        """
        try:
            validated_id = int(metrics_id)
            if validated_id <= 0:
                raise ValueError("L'ID de la métrique doit être positif")
            return validated_id
        except (ValueError, TypeError):
            raise ValueError("L'ID de la métrique doit être un entier valide")
    
    @staticmethod
    def validate_generation_method(method: str) -> str:
        """
        Valide la méthode de génération de recommandations.
        
        Args:
            method: Méthode à valider
            
        Returns:
            str: Méthode validée
        """
        if method not in ['classic', 'llm']:
            return 'classic'  # Méthode par défaut
        return method