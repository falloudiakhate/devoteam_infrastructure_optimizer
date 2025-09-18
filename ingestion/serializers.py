from rest_framework import serializers
from .models import InfrastructureMetrics, AnomalyDetection


class InfrastructureMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer pour les métriques d'infrastructure.
    Gère la conversion entre JSON et modèle Django.
    """
    
    uptime_hours = serializers.ReadOnlyField()
    has_degraded_services = serializers.ReadOnlyField()
    
    class Meta:
        model = InfrastructureMetrics
        fields = [
            'id', 'timestamp', 'created_at',
            'cpu_usage', 'memory_usage', 'latency_ms', 'disk_usage',
            'network_in_kbps', 'network_out_kbps', 'io_wait',
            'thread_count', 'active_connections', 'error_rate',
            'uptime_seconds', 'uptime_hours', 'temperature_celsius',
            'power_consumption_watts', 'service_status',
            'is_anomalous', 'analysis_completed', 'has_degraded_services'
        ]
        read_only_fields = ['id', 'created_at', 'is_anomalous', 'analysis_completed']
    
    def validate_cpu_usage(self, value):
        """Valide que l'usage CPU est entre 0 et 100."""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("L'usage CPU doit être entre 0 et 100%")
        return value
    
    def validate_memory_usage(self, value):
        """Valide que l'usage mémoire est entre 0 et 100."""
        if not (0 <= value <= 100):
            raise serializers.ValidationError("L'usage mémoire doit être entre 0 et 100%")
        return value
    
    def validate_error_rate(self, value):
        """Valide que le taux d'erreur est entre 0 et 1."""
        if not (0 <= value <= 1):
            raise serializers.ValidationError("Le taux d'erreur doit être entre 0 et 1")
        return value


class MetricsIngestionSerializer(serializers.Serializer):
    """
    Serializer spécialisé pour l'ingestion de données JSON.
    Correspond exactement au format d'exemple fourni dans le test.
    """
    
    timestamp = serializers.DateTimeField()
    cpu_usage = serializers.FloatField(min_value=0, max_value=100)
    memory_usage = serializers.FloatField(min_value=0, max_value=100)
    latency_ms = serializers.FloatField(min_value=0)
    disk_usage = serializers.FloatField(min_value=0, max_value=100)
    network_in_kbps = serializers.FloatField(min_value=0)
    network_out_kbps = serializers.FloatField(min_value=0)
    io_wait = serializers.FloatField(min_value=0, max_value=100)
    thread_count = serializers.IntegerField(min_value=0)
    active_connections = serializers.IntegerField(min_value=0)
    error_rate = serializers.FloatField(min_value=0, max_value=1)
    uptime_seconds = serializers.IntegerField(min_value=0)
    temperature_celsius = serializers.FloatField()
    power_consumption_watts = serializers.FloatField(min_value=0)
    service_status = serializers.JSONField()
    
    def validate_service_status(self, value):
        """Validation spécifique du service_status pour l'ingestion."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("service_status doit être un objet JSON")
        
        valid_statuses = ['online', 'degraded', 'offline', 'error']
        for service, status in value.items():
            if status not in valid_statuses:
                raise serializers.ValidationError(
                    f"Statut invalide '{status}' pour le service '{service}'"
                )
        return value


class BatchIngestionResultSerializer(serializers.Serializer):
    """
    Serializer pour les résultats d'ingestion en lot.
    """
    
    total = serializers.IntegerField(read_only=True)
    success = serializers.IntegerField(read_only=True)
    error = serializers.IntegerField(read_only=True)
    errors = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    
    processing_duration_seconds = serializers.FloatField(read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    def get_success_rate(self, obj):
        """Calcule le taux de succès en pourcentage."""
        if obj['total'] == 0:
            return 0
        return round((obj['success'] / obj['total']) * 100, 2)


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détections d'anomalies.
    """
    
    total_anomalies = serializers.ReadOnlyField()
    is_critical = serializers.ReadOnlyField()
    metrics_timestamp = serializers.CharField(source='metrics.timestamp', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'metrics', 'metrics_timestamp', 'detected_at',
            'cpu_anomaly', 'memory_anomaly', 'latency_anomaly',
            'disk_anomaly', 'io_anomaly', 'error_rate_anomaly',
            'temperature_anomaly', 'power_anomaly', 'service_anomaly',
            'anomaly_summary', 'severity_score',
            'total_anomalies', 'is_critical'
        ]
        read_only_fields = ['id', 'detected_at', 'metrics_timestamp']


class SystemStatusSerializer(serializers.Serializer):
    """
    Serializer pour l'état général du système.
    """
    
    total_metrics = serializers.IntegerField(read_only=True)
    analyzed_metrics = serializers.IntegerField(read_only=True)
    pending_analysis = serializers.IntegerField(read_only=True)
    total_anomalies = serializers.IntegerField(read_only=True)
    critical_anomalies = serializers.IntegerField(read_only=True)
    total_reports = serializers.IntegerField(read_only=True)
    urgent_reports = serializers.IntegerField(read_only=True)
    
    last_metric_timestamp = serializers.DateTimeField(read_only=True)
    system_health_score = serializers.IntegerField(read_only=True)
    
    analysis_completion_rate = serializers.SerializerMethodField()
    
    def get_analysis_completion_rate(self, obj):
        """Calcule le taux de completion de l'analyse."""
        if obj['total_metrics'] == 0:
            return 100
        return round((obj['analyzed_metrics'] / obj['total_metrics']) * 100, 2)