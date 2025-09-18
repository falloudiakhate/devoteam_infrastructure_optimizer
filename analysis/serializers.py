from rest_framework import serializers
from ingestion.models import AnomalyDetection


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """
    Serializer pour les détections d'anomalies.
    Spécialisé pour l'app analysis.
    """
    
    total_anomalies = serializers.ReadOnlyField()
    is_critical = serializers.ReadOnlyField()
    metrics_timestamp = serializers.CharField(source='metrics.timestamp', read_only=True)
    metrics_cpu_usage = serializers.FloatField(source='metrics.cpu_usage', read_only=True)
    metrics_memory_usage = serializers.FloatField(source='metrics.memory_usage', read_only=True)
    metrics_latency_ms = serializers.FloatField(source='metrics.latency_ms', read_only=True)
    
    class Meta:
        model = AnomalyDetection
        fields = [
            'id', 'metrics', 'metrics_timestamp', 'detected_at',
            'metrics_cpu_usage', 'metrics_memory_usage', 'metrics_latency_ms',
            'cpu_anomaly', 'memory_anomaly', 'latency_anomaly',
            'disk_anomaly', 'io_anomaly', 'error_rate_anomaly',
            'temperature_anomaly', 'power_anomaly', 'service_anomaly',
            'anomaly_summary', 'severity_score',
            'total_anomalies', 'is_critical'
        ]
        read_only_fields = ['id', 'detected_at', 'metrics_timestamp']


class AnomalyStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques d'anomalies.
    """
    
    total_anomalies = serializers.IntegerField(read_only=True)
    critical_anomalies = serializers.IntegerField(read_only=True)
    recent_anomalies = serializers.IntegerField(read_only=True)
    
    anomaly_types_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    severity_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    average_severity = serializers.FloatField(read_only=True)
    critical_rate = serializers.FloatField(read_only=True)
    
    top_anomaly_causes = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )


class BatchAnalysisResultSerializer(serializers.Serializer):
    """
    Serializer pour les résultats d'analyse en lot.
    """
    
    total = serializers.IntegerField(read_only=True)
    analyzed = serializers.IntegerField(read_only=True)
    errors = serializers.IntegerField(read_only=True)
    
    anomalies_detected = serializers.IntegerField(read_only=True)
    critical_anomalies = serializers.IntegerField(read_only=True)
    
    processing_duration_seconds = serializers.FloatField(read_only=True)
    average_processing_time_ms = serializers.FloatField(read_only=True)
    
    success_rate = serializers.SerializerMethodField()
    
    def get_success_rate(self, obj):
        """Calcule le taux de succès en pourcentage."""
        if obj['total'] == 0:
            return 0
        return round((obj['analyzed'] / obj['total']) * 100, 2)