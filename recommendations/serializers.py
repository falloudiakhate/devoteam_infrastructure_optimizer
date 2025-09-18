from rest_framework import serializers
from .models import RecommendationReport


class RecommendationReportSerializer(serializers.ModelSerializer):
    """
    Serializer pour les rapports de recommandations.
    Spécialisé pour l'app recommendations.
    """
    
    total_recommendations = serializers.ReadOnlyField()
    is_urgent = serializers.ReadOnlyField()
    metrics_timestamp = serializers.CharField(source='metrics.timestamp', read_only=True)
    metrics_cpu_usage = serializers.FloatField(source='metrics.cpu_usage', read_only=True)
    metrics_memory_usage = serializers.FloatField(source='metrics.memory_usage', read_only=True)
    has_anomalies = serializers.BooleanField(source='metrics.is_anomalous', read_only=True)
    
    class Meta:
        model = RecommendationReport
        fields = [
            'id', 'metrics', 'metrics_timestamp', 'generated_at',
            'metrics_cpu_usage', 'metrics_memory_usage', 'has_anomalies',
            'executive_summary', 'detailed_analysis', 'recommendations_json',
            'priority_level', 'estimated_impact', 'implementation_timeframe',
            'is_reviewed', 'feedback',
            'total_recommendations', 'is_urgent'
        ]
        read_only_fields = ['id', 'generated_at', 'metrics_timestamp']


class RecommendationStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques des rapports de recommandations.
    """
    
    total_reports = serializers.IntegerField(read_only=True)
    urgent_reports = serializers.IntegerField(read_only=True)
    reviewed_reports = serializers.IntegerField(read_only=True)
    pending_review = serializers.IntegerField(read_only=True)
    
    priority_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    category_distribution = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    average_recommendations_per_report = serializers.FloatField(read_only=True)
    review_completion_rate = serializers.FloatField(read_only=True)
    
    recent_reports = serializers.IntegerField(read_only=True)
    top_recommendation_categories = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )


class BatchRecommendationResultSerializer(serializers.Serializer):
    """
    Serializer pour les résultats de génération en lot.
    """
    
    total = serializers.IntegerField(read_only=True)
    generated = serializers.IntegerField(read_only=True)
    errors = serializers.IntegerField(read_only=True)
    skipped = serializers.IntegerField(read_only=True)
    
    urgent_reports_generated = serializers.IntegerField(read_only=True)
    processing_duration_seconds = serializers.FloatField(read_only=True)
    
    success_rate = serializers.SerializerMethodField()
    
    def get_success_rate(self, obj):
        """Calcule le taux de succès en pourcentage."""
        if obj['total'] == 0:
            return 0
        return round((obj['generated'] / obj['total']) * 100, 2)


class RecommendationSummarySerializer(serializers.Serializer):
    """
    Serializer pour le résumé consolidé des recommandations.
    """
    
    period_days = serializers.IntegerField(read_only=True)
    total_recommendations = serializers.IntegerField(read_only=True)
    
    top_categories = serializers.ListField(
        child=serializers.DictField(),
        read_only=True
    )
    
    priority_breakdown = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    most_common_issues = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    
    implementation_timeline = serializers.DictField(
        child=serializers.IntegerField(),
        read_only=True
    )
    
    estimated_impact_summary = serializers.CharField(read_only=True)