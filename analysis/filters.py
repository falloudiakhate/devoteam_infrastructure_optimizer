"""
Filtres pour l'API d'analyse des anomalies.
Centralise toute la logique de filtrage des données.
"""

from datetime import timedelta
from django.utils import timezone
from django.db.models import QuerySet
from ingestion.models import AnomalyDetection


class AnomalyFilters:
    """
    Classe pour appliquer des filtres sur les anomalies.
    """
    
    @staticmethod
    def apply_time_filter(queryset: QuerySet, hours: str) -> QuerySet:
        """
        Applique un filtre temporel sur les anomalies.
        
        Args:
            queryset: QuerySet des anomalies
            hours: Nombre d'heures à filtrer (string)
            
        Returns:
            QuerySet filtré
        """
        if not hours:
            return queryset
            
        try:
            hours_ago = timezone.now() - timedelta(hours=int(hours))
            return queryset.filter(detected_at__gte=hours_ago)
        except (ValueError, TypeError):
            return queryset
    
    @staticmethod
    def apply_severity_filter(queryset: QuerySet, min_severity: str) -> QuerySet:
        """
        Applique un filtre de sévérité minimale.
        
        Args:
            queryset: QuerySet des anomalies
            min_severity: Score de sévérité minimum (string)
            
        Returns:
            QuerySet filtré
        """
        if not min_severity:
            return queryset
            
        try:
            min_score = int(min_severity)
            if 1 <= min_score <= 10:
                return queryset.filter(severity_score__gte=min_score)
        except (ValueError, TypeError):
            pass
            
        return queryset
    
    @staticmethod
    def apply_critical_filter(queryset: QuerySet, critical_only: str) -> QuerySet:
        """
        Applique un filtre pour ne garder que les anomalies critiques.
        
        Args:
            queryset: QuerySet des anomalies
            critical_only: Si 'true', ne garde que les critiques
            
        Returns:
            QuerySet filtré
        """
        if critical_only and critical_only.lower() == 'true':
            return queryset.filter(severity_score__gte=7)
        return queryset
    
    @staticmethod
    def apply_limit_filter(queryset: QuerySet, limit: str, default_limit: int = 50) -> QuerySet:
        """
        Applique une limitation du nombre de résultats.
        
        Args:
            queryset: QuerySet des anomalies
            limit: Nombre maximum de résultats (string)
            default_limit: Limite par défaut
            
        Returns:
            QuerySet limité
        """
        try:
            max_results = int(limit) if limit else default_limit
            max_results = min(max_results, 500)  # Limite absolue de sécurité
            return queryset[:max_results]
        except (ValueError, TypeError):
            return queryset[:default_limit]
    
    @staticmethod
    def get_filtered_anomalies(request_params: dict) -> QuerySet:
        """
        Applique tous les filtres sur les anomalies selon les paramètres de requête.
        
        Args:
            request_params: Dictionnaire des paramètres de requête
            
        Returns:
            QuerySet filtré et ordonné
        """
        queryset = AnomalyDetection.objects.all()
        
        # Application des filtres
        queryset = AnomalyFilters.apply_time_filter(
            queryset, 
            request_params.get('hours')
        )
        
        queryset = AnomalyFilters.apply_severity_filter(
            queryset, 
            request_params.get('min_severity')
        )
        
        queryset = AnomalyFilters.apply_critical_filter(
            queryset, 
            request_params.get('critical_only')
        )
        
        # Tri par date de détection (plus récent d'abord)
        queryset = queryset.order_by('-detected_at')
        
        # Application de la limite
        queryset = AnomalyFilters.apply_limit_filter(
            queryset, 
            request_params.get('limit')
        )
        
        return queryset
    
    @staticmethod
    def get_filter_info(request_params: dict) -> dict:
        """
        Retourne les informations sur les filtres appliqués.
        
        Args:
            request_params: Dictionnaire des paramètres de requête
            
        Returns:
            Dictionnaire avec les informations des filtres
        """
        return {
            'hours_filter': request_params.get('hours'),
            'min_severity': request_params.get('min_severity'),
            'critical_only': request_params.get('critical_only', '').lower() == 'true',
            'limit': request_params.get('limit', '50')
        }


class MetricsFilters:
    """
    Classe pour appliquer des filtres sur les métriques.
    """
    
    @staticmethod
    def get_unanalyzed_metrics():
        """
        Retourne les métriques non analysées.
        
        Returns:
            QuerySet des métriques non analysées
        """
        from ingestion.models import InfrastructureMetrics
        return InfrastructureMetrics.objects.filter(analysis_completed=False)
    
    @staticmethod
    def validate_metrics_id(metrics_id: str) -> int:
        """
        Valide et convertit un ID de métrique.
        
        Args:
            metrics_id: ID de la métrique (string)
            
        Returns:
            ID de la métrique (int)
            
        Raises:
            ValueError: Si l'ID n'est pas valide
        """
        if not metrics_id:
            raise ValueError("L'ID de la métrique est requis")
            
        try:
            return int(metrics_id)
        except (ValueError, TypeError):
            raise ValueError("L'ID de la métrique doit être un nombre entier")
    
    @staticmethod
    def validate_analysis_method(method: str) -> str:
        """
        Valide la méthode d'analyse.
        
        Args:
            method: Méthode d'analyse
            
        Returns:
            Méthode validée
        """
        if not method:
            return 'classic'
            
        if method.lower() in ['classic', 'llm']:
            return method.lower()
        
        return 'classic'  # Valeur par défaut si méthode invalide