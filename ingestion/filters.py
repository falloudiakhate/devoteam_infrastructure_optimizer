"""
Filtres pour l'application d'ingestion.
Centralise la logique de filtrage et validation pour les données d'ingestion.
"""

from typing import Dict, Any, List
from django.db.models import QuerySet
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import InfrastructureMetrics


class IngestionFilters:
    """
    Filtres pour les données d'ingestion et métriques.
    """
    
    @staticmethod
    def get_recent_metrics(hours: int = 24) -> QuerySet:
        """
        Récupère les métriques récentes.
        
        Args:
            hours: Nombre d'heures à récupérer
            
        Returns:
            QuerySet: Métriques récentes
        """
        time_threshold = timezone.now() - timedelta(hours=hours)
        return InfrastructureMetrics.objects.filter(
            timestamp__gte=time_threshold
        ).order_by('-timestamp')
    
    @staticmethod
    def get_metrics_by_status(analyzed: bool = None, anomalous: bool = None) -> QuerySet:
        """
        Récupère les métriques par statut d'analyse.
        
        Args:
            analyzed: True pour les métriques analysées, False pour non analysées
            anomalous: True pour les métriques avec anomalies
            
        Returns:
            QuerySet: Métriques filtrées
        """
        queryset = InfrastructureMetrics.objects.all()
        
        if analyzed is not None:
            queryset = queryset.filter(analysis_completed=analyzed)
        
        if anomalous is not None:
            queryset = queryset.filter(is_anomalous=anomalous)
            
        return queryset.order_by('-timestamp')
    
    @staticmethod
    def get_metrics_requiring_analysis() -> QuerySet:
        """
        Récupère les métriques nécessitant une analyse.
        
        Returns:
            QuerySet: Métriques non analysées
        """
        return InfrastructureMetrics.objects.filter(
            analysis_completed=False
        ).order_by('timestamp')
    
    @staticmethod
    def get_high_resource_usage_metrics(
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        disk_threshold: float = 80.0
    ) -> QuerySet:
        """
        Récupère les métriques avec utilisation élevée des ressources.
        
        Args:
            cpu_threshold: Seuil CPU en pourcentage
            memory_threshold: Seuil mémoire en pourcentage  
            disk_threshold: Seuil disque en pourcentage
            
        Returns:
            QuerySet: Métriques avec utilisation élevée
        """
        from django.db.models import Q
        
        return InfrastructureMetrics.objects.filter(
            Q(cpu_usage__gte=cpu_threshold) |
            Q(memory_usage__gte=memory_threshold) |
            Q(disk_usage__gte=disk_threshold)
        ).order_by('-timestamp')


class ValidationFilters:
    """
    Filtres pour la validation des données d'ingestion.
    """
    
    REQUIRED_FIELDS = [
        'timestamp', 'cpu_usage', 'memory_usage', 'latency_ms',
        'disk_usage', 'network_in_kbps', 'network_out_kbps',
        'io_wait', 'thread_count', 'active_connections', 
        'error_rate', 'uptime_seconds', 'temperature_celsius',
        'power_consumption_watts', 'service_status'
    ]
    
    PERCENTAGE_FIELDS = ['cpu_usage', 'memory_usage', 'disk_usage', 'io_wait']
    
    POSITIVE_FIELDS = [
        'latency_ms', 'network_in_kbps', 'network_out_kbps',
        'thread_count', 'active_connections', 'uptime_seconds',
        'power_consumption_watts'
    ]
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any]) -> List[str]:
        """
        Valide la présence des champs obligatoires.
        
        Args:
            data: Données à valider
            
        Returns:
            List[str]: Liste des champs manquants
        """
        missing_fields = []
        for field in ValidationFilters.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any]) -> List[str]:
        """
        Valide les types de données.
        
        Args:
            data: Données à valider
            
        Returns:
            List[str]: Liste des erreurs de type
        """
        type_errors = []
        
        # Validation des champs numériques
        numeric_fields = [
            'cpu_usage', 'memory_usage', 'latency_ms', 'disk_usage',
            'network_in_kbps', 'network_out_kbps', 'io_wait',
            'error_rate', 'temperature_celsius', 'power_consumption_watts'
        ]
        
        for field in numeric_fields:
            if field in data:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    type_errors.append(f"{field} doit être un nombre")
        
        # Validation des champs entiers
        integer_fields = ['thread_count', 'active_connections', 'uptime_seconds']
        for field in integer_fields:
            if field in data:
                try:
                    int(data[field])
                except (ValueError, TypeError):
                    type_errors.append(f"{field} doit être un entier")
        
        # Validation du service_status
        if 'service_status' in data:
            if not isinstance(data['service_status'], dict):
                type_errors.append("service_status doit être un objet JSON")
        
        return type_errors
    
    @staticmethod
    def validate_field_ranges(data: Dict[str, Any]) -> List[str]:
        """
        Valide les plages de valeurs.
        
        Args:
            data: Données à valider
            
        Returns:
            List[str]: Liste des erreurs de plage
        """
        range_errors = []
        
        # Validation des pourcentages (0-100)
        for field in ValidationFilters.PERCENTAGE_FIELDS:
            if field in data:
                try:
                    value = float(data[field])
                    if not (0 <= value <= 100):
                        range_errors.append(f"{field} doit être entre 0 et 100 (reçu: {value})")
                except (ValueError, TypeError):
                    pass  # Erreur de type déjà gérée ailleurs
        
        # Validation du taux d'erreur (0-1)
        if 'error_rate' in data:
            try:
                value = float(data['error_rate'])
                if not (0 <= value <= 1):
                    range_errors.append(f"error_rate doit être entre 0 et 1 (reçu: {value})")
            except (ValueError, TypeError):
                pass
        
        # Validation des valeurs positives
        for field in ValidationFilters.POSITIVE_FIELDS:
            if field in data:
                try:
                    value = float(data[field]) if field not in ['thread_count', 'active_connections', 'uptime_seconds'] else int(data[field])
                    if value < 0:
                        range_errors.append(f"{field} ne peut pas être négatif (reçu: {value})")
                except (ValueError, TypeError):
                    pass
        
        return range_errors
    
    @staticmethod
    def validate_timestamp(timestamp_input) -> tuple[datetime, str]:
        """
        Valide et parse le timestamp.
        
        Args:
            timestamp_input: Timestamp à valider
            
        Returns:
            tuple[datetime, str]: (timestamp parsé, message d'erreur si applicable)
        """
        try:
            # Si c'est déjà un objet datetime
            if isinstance(timestamp_input, datetime):
                return timestamp_input, ""
            
            # Traitement comme chaîne
            timestamp_str = str(timestamp_input)
            
            # Gestion du format ISO 8601 avec Z
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            parsed_timestamp = datetime.fromisoformat(timestamp_str)
            
            # Vérifier que le timestamp n'est pas dans le futur
            if parsed_timestamp > timezone.now():
                return parsed_timestamp, "Le timestamp ne peut pas être dans le futur"
            
            return parsed_timestamp, ""
            
        except (ValueError, AttributeError) as e:
            return timezone.now(), f"Format de timestamp invalide: {str(e)}"
    
    @staticmethod
    def validate_service_status(service_status: Dict[str, Any]) -> List[str]:
        """
        Valide la structure du service_status.
        
        Args:
            service_status: Dictionnaire du statut des services
            
        Returns:
            List[str]: Liste des erreurs de validation
        """
        errors = []
        
        if not isinstance(service_status, dict):
            return ["service_status doit être un dictionnaire"]
        
        # Valeurs acceptées pour les statuts
        valid_statuses = ['online', 'offline', 'degraded', 'error', 'maintenance']
        
        for service_name, status in service_status.items():
            if not isinstance(service_name, str):
                errors.append(f"Nom de service invalide: {service_name}")
                continue
                
            if status not in valid_statuses:
                errors.append(
                    f"Statut invalide pour {service_name}: {status}. "
                    f"Valeurs acceptées: {', '.join(valid_statuses)}"
                )
        
        return errors
    
    @staticmethod
    def validate_metrics_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validation complète des données de métriques.
        
        Args:
            data: Données à valider
            
        Returns:
            Dict[str, List[str]]: Dictionnaire des erreurs par catégorie
        """
        validation_errors = {
            'missing_fields': ValidationFilters.validate_required_fields(data),
            'type_errors': ValidationFilters.validate_field_types(data),
            'range_errors': ValidationFilters.validate_field_ranges(data),
            'timestamp_errors': [],
            'service_status_errors': []
        }
        
        # Validation du timestamp
        if 'timestamp' in data:
            _, timestamp_error = ValidationFilters.validate_timestamp(data['timestamp'])
            if timestamp_error:
                validation_errors['timestamp_errors'].append(timestamp_error)
        
        # Validation du service_status
        if 'service_status' in data:
            service_errors = ValidationFilters.validate_service_status(data['service_status'])
            validation_errors['service_status_errors'].extend(service_errors)
        
        return validation_errors
    
    @staticmethod
    def has_validation_errors(validation_result: Dict[str, List[str]]) -> bool:
        """
        Vérifie s'il y a des erreurs de validation.
        
        Args:
            validation_result: Résultat de la validation
            
        Returns:
            bool: True s'il y a des erreurs
        """
        return any(errors for errors in validation_result.values())
    
    @staticmethod
    def format_validation_errors(validation_result: Dict[str, List[str]]) -> List[str]:
        """
        Formate les erreurs de validation en liste lisible.
        
        Args:
            validation_result: Résultat de la validation
            
        Returns:
            List[str]: Liste des erreurs formatées
        """
        formatted_errors = []
        
        for category, errors in validation_result.items():
            if errors:
                category_name = category.replace('_', ' ').title()
                formatted_errors.extend([f"{category_name}: {error}" for error in errors])
        
        return formatted_errors