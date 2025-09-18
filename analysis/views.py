import time
import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from ingestion.models import InfrastructureMetrics, AnomalyDetection
from .services import AnomalyDetectionService
from .serializers import BatchAnalysisResultSerializer
from .swagger import AnalysisSwaggerSchemas
from .filters import AnomalyFilters, MetricsFilters
from .codes import APIResponse, ResponseCodes, ResponseMessages

logger = logging.getLogger(__name__)


class AnomalyAnalysisView(APIView):
    """
    Vue pour l'analyse d'anomalies (métrique unique ou lot).
    """
    
    @AnalysisSwaggerSchemas.get_analyze_schema()
    def post(self, request):
        """
        Lance l'analyse d'anomalies pour une métrique spécifique ou toutes les métriques non analysées.
        """
        try:
            start_time = time.time()
            metrics_id = request.query_params.get('metrics_id')
            method = MetricsFilters.validate_analysis_method(
                request.query_params.get('method', 'classic')
            )
            
            if metrics_id:
                return self._analyze_single_metric(metrics_id, method, start_time)
            else:
                return self._analyze_batch_metrics(method, start_time)
                
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur lors de l'analyse")
    
    def _analyze_single_metric(self, metrics_id, method, start_time):
        """Analyse une métrique spécifique."""
        try:
            # Validation de l'ID
            validated_id = MetricsFilters.validate_metrics_id(metrics_id)
            metrics = get_object_or_404(InfrastructureMetrics, id=validated_id)
            
            # Vérification si déjà analysé avec la même méthode
            if metrics.analysis_completed and hasattr(metrics, 'anomaly_detection'):
                existing_analysis = metrics.anomaly_detection
                
                # Si même méthode, retourner l'analyse existante
                if existing_analysis.analysis_method == method:
                    return APIResponse.analysis_already_exists(
                        metrics_id=metrics.id,
                        analysis_id=existing_analysis.id,
                        anomaly_detection=existing_analysis
                    )
                
                # Si méthode différente, supprimer l'ancienne analyse pour la refaire
                logger.info(f"Re-analyse métrique {metrics.id} avec méthode {method} (ancienne: {existing_analysis.analysis_method})")
                existing_analysis.delete()
                metrics.analysis_completed = False
                metrics.is_anomalous = False
                metrics.save()
            
            # Analyse de la métrique
            anomaly_service = AnomalyDetectionService(method=method)
            anomaly_detection = anomaly_service.analyze_metrics(metrics)
            
            if not anomaly_detection:
                # Si méthode LLM et non configuré, message spécifique
                if method == 'llm':
                    return APIResponse.error(
                        message=ResponseMessages.LLM_NOT_CONFIGURED_MSG,
                        code=ResponseCodes.LLM_NOT_CONFIGURED,
                        status_code=400
                    )
                else:
                    return APIResponse.error(
                        message=ResponseMessages.ANALYSIS_FAILED_MSG,
                        code=ResponseCodes.ANALYSIS_FAILED
                    )
            
            # Retour du succès
            processing_time = (time.time() - start_time)
            return APIResponse.analysis_success(
                metrics_id=metrics.id,
                analysis_id=anomaly_detection.id,
                anomalies_detected=anomaly_detection.total_anomalies,
                severity_score=anomaly_detection.severity_score,
                is_critical=anomaly_detection.is_critical,
                anomaly_summary=anomaly_detection.anomaly_summary,
                processing_time=processing_time,
                method_used=method,
                method_info=anomaly_service.get_method_info()
            )
                
        except ValueError as e:
            return APIResponse.validation_error(str(e))
        except InfrastructureMetrics.DoesNotExist:
            return APIResponse.not_found("Métrique", metrics_id)
        except Exception as e:
            return APIResponse.handle_exception(e, f"Erreur analyse métrique {metrics_id}")
    
    def _analyze_batch_metrics(self, method, start_time):
        """Analyse toutes les métriques non analysées."""
        try:
            # Récupération des métriques non analysées
            unanalyzed_metrics = MetricsFilters.get_unanalyzed_metrics()
            
            if not unanalyzed_metrics.exists():
                return APIResponse.success(
                    message=ResponseMessages.NO_METRICS_PENDING,
                    data={
                        'total': 0,
                        'analyzed': 0,
                        'errors': 0,
                        'method_used': method
                    },
                    code=ResponseCodes.NO_METRICS_TO_ANALYZE
                )
            
            # Lancement de l'analyse en lot
            anomaly_service = AnomalyDetectionService(method=method)
            results = anomaly_service.analyze_batch_metrics(unanalyzed_metrics)
            
            # Calcul des statistiques d'anomalies
            total_anomalies = 0
            critical_anomalies = 0
            
            for metrics in unanalyzed_metrics:
                if hasattr(metrics, 'anomaly_detection'):
                    detection = metrics.anomaly_detection
                    total_anomalies += detection.total_anomalies
                    if detection.is_critical:
                        critical_anomalies += 1
            
            # Finalisation des résultats
            processing_duration = time.time() - start_time
            results.update({
                'anomalies_detected': total_anomalies,
                'critical_anomalies': critical_anomalies,
                'processing_duration_seconds': round(processing_duration, 3),
                'average_processing_time_ms': round((processing_duration / max(results['total'], 1)) * 1000, 2),
                'method_used': method,
                'method_info': anomaly_service.get_method_info()
            })
            
            serializer = BatchAnalysisResultSerializer(results)
            return APIResponse.success(
                message=ResponseMessages.BATCH_ANALYSIS_SUCCESS,
                data=serializer.data,
                code=ResponseCodes.ANALYSIS_COMPLETED
            )
            
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur analyse en lot")


class AnomalyResultView(APIView):
    """
    Vue pour récupérer les résultats d'une analyse d'anomalies existante.
    """
    
    @AnalysisSwaggerSchemas.get_result_schema()
    def get(self, request, analysis_id):
        """
        Récupère les résultats d'une analyse d'anomalies existante.
        """
        try:
            # Récupération de l'analyse
            anomaly_detection = get_object_or_404(AnomalyDetection, id=analysis_id)
            
            # Construction de la réponse
            response_data = {
                'analysis_id': anomaly_detection.id,
                'metrics_id': anomaly_detection.metrics.id,
                'detected_at': anomaly_detection.detected_at,
                'anomalies_detected': anomaly_detection.total_anomalies,
                'severity_score': anomaly_detection.severity_score,
                'is_critical': anomaly_detection.is_critical,
                'anomaly_summary': anomaly_detection.anomaly_summary,
                'analysis_method': anomaly_detection.analysis_method,
                'anomaly_details': {
                    'cpu_anomaly': anomaly_detection.cpu_anomaly,
                    'memory_anomaly': anomaly_detection.memory_anomaly,
                    'latency_anomaly': anomaly_detection.latency_anomaly,
                    'disk_anomaly': anomaly_detection.disk_anomaly,
                    'io_anomaly': anomaly_detection.io_anomaly,
                    'error_rate_anomaly': anomaly_detection.error_rate_anomaly,
                    'temperature_anomaly': anomaly_detection.temperature_anomaly,
                    'power_anomaly': anomaly_detection.power_anomaly,
                    'service_anomaly': anomaly_detection.service_anomaly
                },
                'metrics_data': {
                    'timestamp': anomaly_detection.metrics.timestamp,
                    'cpu_usage': anomaly_detection.metrics.cpu_usage,
                    'memory_usage': anomaly_detection.metrics.memory_usage,
                    'latency_ms': anomaly_detection.metrics.latency_ms,
                    'disk_usage': anomaly_detection.metrics.disk_usage,
                    'network_in_kbps': anomaly_detection.metrics.network_in_kbps,
                    'network_out_kbps': anomaly_detection.metrics.network_out_kbps,
                    'io_wait': anomaly_detection.metrics.io_wait,
                    'thread_count': anomaly_detection.metrics.thread_count,
                    'active_connections': anomaly_detection.metrics.active_connections,
                    'error_rate': anomaly_detection.metrics.error_rate,
                    'uptime_seconds': anomaly_detection.metrics.uptime_seconds,
                    'temperature_celsius': anomaly_detection.metrics.temperature_celsius,
                    'power_consumption_watts': anomaly_detection.metrics.power_consumption_watts,
                    'service_status': anomaly_detection.metrics.service_status
                }
            }
            
            return APIResponse.success(
                message="Analyse récupérée avec succès",
                data=response_data
            )
            
        except AnomalyDetection.DoesNotExist:
            return APIResponse.not_found("Analyse", str(analysis_id))
        except Exception as e:
            return APIResponse.handle_exception(e, f"Erreur récupération analyse {analysis_id}")


class AnomalyListView(APIView):
    """
    Vue pour lister toutes les anomalies avec filtres optionnels.
    """
    
    @AnalysisSwaggerSchemas.get_anomalies_list_schema()
    def get(self, request):
        """
        Récupère la liste des anomalies avec filtres optionnels.
        """
        try:
            # Application des filtres
            queryset = AnomalyFilters.get_filtered_anomalies(request.query_params)
            
            # Construction de la réponse
            anomalies_list = []
            for anomaly in queryset:
                anomaly_data = {
                    'analysis_id': anomaly.id,
                    'metrics_id': anomaly.metrics.id,
                    'detected_at': anomaly.detected_at,
                    'anomalies_detected': anomaly.total_anomalies,
                    'severity_score': anomaly.severity_score,
                    'is_critical': anomaly.is_critical,
                    'anomaly_summary': anomaly.anomaly_summary,
                    'analysis_method': anomaly.analysis_method,
                    'anomaly_types': [
                        'cpu' if anomaly.cpu_anomaly else None,
                        'memory' if anomaly.memory_anomaly else None,
                        'latency' if anomaly.latency_anomaly else None,
                        'disk' if anomaly.disk_anomaly else None,
                        'io' if anomaly.io_anomaly else None,
                        'error_rate' if anomaly.error_rate_anomaly else None,
                        'temperature' if anomaly.temperature_anomaly else None,
                        'power' if anomaly.power_anomaly else None,
                        'service' if anomaly.service_anomaly else None
                    ],
                    'metrics_timestamp': anomaly.metrics.timestamp
                }
                # Nettoyer les types None
                anomaly_data['anomaly_types'] = [t for t in anomaly_data['anomaly_types'] if t is not None]
                anomalies_list.append(anomaly_data)
            
            # Statistiques globales
            from django.utils import timezone
            from datetime import timedelta
            
            total_anomalies = AnomalyDetection.objects.count()
            critical_count = AnomalyDetection.objects.filter(severity_score__gte=7).count()
            recent_count = AnomalyDetection.objects.filter(
                detected_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Informations sur les filtres appliqués
            filter_info = AnomalyFilters.get_filter_info(request.query_params)
            limit = int(request.query_params.get('limit', 50))
            
            response_data = {
                'anomalies': anomalies_list,
                'pagination': {
                    'returned_count': len(anomalies_list),
                    'requested_limit': limit,
                    'has_more': len(anomalies_list) == limit
                },
                'statistics': {
                    'total_anomalies_all_time': total_anomalies,
                    'critical_anomalies_all_time': critical_count,
                    'recent_anomalies_24h': recent_count
                },
                'filters_applied': filter_info
            }
            
            return APIResponse.success(
                message=f"{len(anomalies_list)} anomalies récupérées",
                data=response_data
            )
            
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur récupération liste anomalies")


