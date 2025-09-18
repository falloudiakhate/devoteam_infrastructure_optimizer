"""
Vues pour l'interface frontend du dashboard.
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from ingestion.models import InfrastructureMetrics, AnomalyDetection
from recommendations.models import RecommendationReport


class DashboardView(TemplateView):
    """
    Vue principale du dashboard d'optimisation d'infrastructure.
    """
    template_name = 'frontend/dashboard.html'


class SimpleDashboardView(TemplateView):
    """
    Vue du dashboard simplifié avec workflow étape par étape.
    """
    template_name = 'frontend/modern_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context.update({
            'total_metrics': InfrastructureMetrics.objects.count(),
            'total_analyses': AnomalyDetection.objects.count(),
            'total_recommendations': RecommendationReport.objects.count(),
            'anomalous_metrics': InfrastructureMetrics.objects.filter(is_anomalous=True).count(),
        })
        
        return context


class DashboardStatsView(TemplateView):
    """
    API pour récupérer les statistiques du dashboard.
    """
    
    def get(self, request, *args, **kwargs):
        """Retourne les statistiques actuelles du système."""
        
        # Métriques récentes (dernières 24h)
        from django.utils import timezone
        from datetime import timedelta
        
        recent_time = timezone.now() - timedelta(hours=24)
        
        stats = {
            'metrics': {
                'total': InfrastructureMetrics.objects.count(),
                'recent': InfrastructureMetrics.objects.filter(
                    timestamp__gte=recent_time
                ).count(),
                'anomalous': InfrastructureMetrics.objects.filter(
                    is_anomalous=True
                ).count(),
                'analyzed': InfrastructureMetrics.objects.filter(
                    analysis_completed=True
                ).count(),
            },
            'analysis': {
                'total': AnomalyDetection.objects.count(),
                'recent': AnomalyDetection.objects.filter(
                    created_at__gte=recent_time
                ).count(),
                'critical': AnomalyDetection.objects.filter(
                    severity_score__gte=8
                ).count(),
            },
            'recommendations': {
                'total': RecommendationReport.objects.count(),
                'recent': RecommendationReport.objects.filter(
                    created_at__gte=recent_time
                ).count(),
                'high_priority': RecommendationReport.objects.filter(
                    priority_level__in=['high', 'critical']
                ).count(),
            }
        }
        
        return JsonResponse({
            'success': True,
            'data': stats
        })


@method_decorator(csrf_exempt, name='dispatch')
class QuickTestView(TemplateView):
    """
    Vue pour tester rapidement les endpoints avec des données d'exemple.
    """
    
    def post(self, request, *args, **kwargs):
        """Injecte des données de test pour démonstration."""
        
        try:
            # Données de test
            sample_metrics = [
                {
                    "timestamp": "2023-10-01T12:00:00Z",
                    "cpu_usage": 85.5,
                    "memory_usage": 78.2,
                    "latency_ms": 250,
                    "disk_usage": 65.0,
                    "network_in_kbps": 1500,
                    "network_out_kbps": 1200,
                    "io_wait": 12.5,
                    "thread_count": 150,
                    "active_connections": 45,
                    "error_rate": 0.05,
                    "uptime_seconds": 360000,
                    "temperature_celsius": 68.5,
                    "power_consumption_watts": 280,
                    "service_status": {
                        "database": "degraded",
                        "api_gateway": "online", 
                        "cache": "offline"
                    }
                },
                {
                    "timestamp": "2023-10-01T12:15:00Z",
                    "cpu_usage": 92.1,
                    "memory_usage": 88.7,
                    "latency_ms": 450,
                    "disk_usage": 82.3,
                    "network_in_kbps": 2800,
                    "network_out_kbps": 2100,
                    "io_wait": 25.8,
                    "thread_count": 200,
                    "active_connections": 78,
                    "error_rate": 0.12,
                    "uptime_seconds": 361000,
                    "temperature_celsius": 78.2,
                    "power_consumption_watts": 420,
                    "service_status": {
                        "database": "error",
                        "api_gateway": "degraded",
                        "cache": "offline"
                    }
                }
            ]
            
            # Ingestion des données de test
            from ingestion.services import DataIngestionService
            ingestion_service = DataIngestionService()
            
            results = []
            for metrics_data in sample_metrics:
                try:
                    metrics = ingestion_service.ingest_metrics_data(metrics_data)
                    if metrics:
                        results.append({
                            'metrics_id': metrics.id,
                            'timestamp': str(metrics.timestamp),
                            'status': 'success'
                        })
                except Exception as e:
                    results.append({
                        'error': str(e),
                        'status': 'error'
                    })
            
            return JsonResponse({
                'success': True,
                'message': f'Données de test injectées: {len(results)} métriques',
                'data': results
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class SystemHealthView(TemplateView):
    """
    Vue pour vérifier l'état de santé du système.
    """
    
    def get(self, request, *args, **kwargs):
        """Retourne l'état de santé du système."""
        
        try:
            # Vérifications de base
            health_checks = {
                'database': self._check_database(),
                'ingestion_service': self._check_ingestion_service(),
                'analysis_service': self._check_analysis_service(),
                'recommendation_service': self._check_recommendation_service(),
            }
            
            # Statut global
            all_healthy = all(check['status'] == 'healthy' for check in health_checks.values())
            
            return JsonResponse({
                'success': True,
                'status': 'healthy' if all_healthy else 'degraded',
                'checks': health_checks,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)
    
    def _check_database(self):
        """Vérifie la connectivité à la base de données."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }
    
    def _check_ingestion_service(self):
        """Vérifie le service d'ingestion."""
        try:
            from ingestion.services import DataIngestionService
            service = DataIngestionService()
            # Test basique du service
            return {
                'status': 'healthy',
                'message': 'Ingestion service available'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Ingestion service error: {str(e)}'
            }
    
    def _check_analysis_service(self):
        """Vérifie le service d'analyse."""
        try:
            from analysis.services import AnomalyDetectionService
            service = AnomalyDetectionService()
            return {
                'status': 'healthy',
                'message': 'Analysis service available'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Analysis service error: {str(e)}'
            }
    
    def _check_recommendation_service(self):
        """Vérifie le service de recommandations."""
        try:
            from recommendations.services import RecommendationService
            service = RecommendationService()
            return {
                'status': 'healthy',
                'message': 'Recommendation service available'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Recommendation service error: {str(e)}'
            }