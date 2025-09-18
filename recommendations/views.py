import time
import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from ingestion.models import InfrastructureMetrics
from recommendations.models import RecommendationReport
from .services import RecommendationService
from .serializers import BatchRecommendationResultSerializer
from .swagger import RecommendationSwaggerSchemas
from .filters import RecommendationFilters, MetricsFilters
from .codes import APIResponse, ResponseCodes, ResponseMessages

logger = logging.getLogger(__name__)


class RecommendationGenerationView(APIView):
    """
    Vue pour la génération de recommandations (métrique unique ou lot).
    """
    
    @RecommendationSwaggerSchemas.get_generate_schema()
    def post(self, request):
        """
        Lance la génération de recommandations pour une métrique spécifique ou toutes les métriques analysées.
        """
        try:
            start_time = time.time()
            metrics_id = request.query_params.get('metrics_id')
            method = MetricsFilters.validate_generation_method(
                request.query_params.get('method', 'classic')
            )
            
            if metrics_id:
                return self._generate_single_recommendation(metrics_id, method, start_time)
            else:
                return self._generate_batch_recommendations(method, start_time)
                
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur lors de la génération")
    
    def _generate_single_recommendation(self, metrics_id, method, start_time):
        """Génère des recommandations pour une métrique spécifique."""
        try:
            # Validation de l'ID
            validated_id = MetricsFilters.validate_metrics_id(metrics_id)
            metrics = get_object_or_404(InfrastructureMetrics, id=validated_id)
            
            # Vérifier que la métrique a été analysée
            if not metrics.analysis_completed:
                return APIResponse.error(
                    message=ResponseMessages.METRICS_NOT_ANALYZED_MSG,
                    code=ResponseCodes.METRICS_NOT_ANALYZED,
                    status_code=400
                )
            
            # Vérification si rapport déjà existant
            if hasattr(metrics, 'recommendation_report'):
                existing_report = metrics.recommendation_report
                
                # Si même méthode, retourner le rapport existant
                if existing_report.generation_method == method:
                    return APIResponse.report_already_exists(
                        metrics_id=metrics.id,
                        report_id=existing_report.id,
                        report=existing_report
                    )
                
                # Si méthode différente, supprimer l'ancien rapport pour le refaire
                logger.info(f"Re-génération rapport {metrics.id} avec méthode {method} (ancienne: {existing_report.generation_method})")
                existing_report.delete()
            
            # Génération du rapport
            recommendation_service = RecommendationService(method=method)
            report = recommendation_service.generate_recommendation_report(metrics)
            
            if not report:
                # Si méthode LLM et non configuré, message spécifique
                if method == 'llm':
                    return APIResponse.error(
                        message=ResponseMessages.LLM_NOT_CONFIGURED_MSG,
                        code=ResponseCodes.LLM_NOT_CONFIGURED,
                        status_code=400
                    )
                else:
                    return APIResponse.error(
                        message=ResponseMessages.GENERATION_FAILED_MSG,
                        code=ResponseCodes.GENERATION_FAILED
                    )
            
            # Retour du succès
            processing_time = (time.time() - start_time)
            return APIResponse.generation_success(
                metrics_id=metrics.id,
                report_id=report.id,
                recommendations_count=len(report.recommendations) if hasattr(report, 'recommendations') else 0,
                priority_level=report.priority_level,
                is_urgent=report.is_urgent,
                processing_time=processing_time,
                method_used=method,
                method_info=recommendation_service.get_method_info()
            )
                
        except ValueError as e:
            return APIResponse.validation_error(str(e))
        except InfrastructureMetrics.DoesNotExist:
            return APIResponse.not_found("Métrique", metrics_id)
        except Exception as e:
            return APIResponse.handle_exception(e, f"Erreur génération rapport métrique {metrics_id}")
    
    def _generate_batch_recommendations(self, method, start_time):
        """Génère des recommandations pour toutes les métriques sans rapport."""
        try:
            # Récupération des métriques sans rapport
            metrics_without_reports = MetricsFilters.get_metrics_without_reports()
            
            if not metrics_without_reports.exists():
                return APIResponse.success(
                    message=ResponseMessages.NO_METRICS_PENDING,
                    data={
                        'total': 0,
                        'generated': 0,
                        'errors': 0,
                        'method_used': method
                    },
                    code=ResponseCodes.NO_METRICS_FOR_RECOMMENDATIONS
                )
            
            # Lancement de la génération en lot
            recommendation_service = RecommendationService(method=method)
            results = recommendation_service.generate_batch_reports(metrics_without_reports)
            
            # Calcul des statistiques de recommandations
            urgent_reports = 0
            total_recommendations = 0
            
            for metrics in metrics_without_reports:
                if hasattr(metrics, 'recommendation_report'):
                    report = metrics.recommendation_report
                    if report.is_urgent:
                        urgent_reports += 1
                    total_recommendations += len(report.recommendations) if hasattr(report, 'recommendations') else 0
            
            # Finalisation des résultats
            processing_duration = time.time() - start_time
            results.update({
                'urgent_reports': urgent_reports,
                'total_recommendations': total_recommendations,
                'processing_duration_seconds': round(processing_duration, 3),
                'average_processing_time_ms': round((processing_duration / max(results['total'], 1)) * 1000, 2),
                'method_used': method,
                'method_info': recommendation_service.get_method_info()
            })
            
            serializer = BatchRecommendationResultSerializer(results)
            return APIResponse.success(
                message=ResponseMessages.BATCH_GENERATION_SUCCESS,
                data=serializer.data,
                code=ResponseCodes.RECOMMENDATIONS_GENERATED
            )
            
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur génération en lot")


class RecommendationResultView(APIView):
    """
    Vue pour récupérer les résultats d'un rapport de recommandations existant.
    """
    
    @RecommendationSwaggerSchemas.get_result_schema()
    def get(self, request, report_id):
        """
        Récupère les résultats d'un rapport de recommandations existant.
        """
        try:
            # Récupération du rapport
            report = get_object_or_404(RecommendationReport, id=report_id)
            
            # Construction de la réponse
            response_data = {
                'report_id': report.id,
                'metrics_id': report.metrics.id,
                'generated_at': report.generated_at,
                'priority_level': report.priority_level,
                'is_urgent': report.is_urgent,
                'executive_summary': report.executive_summary,
                'detailed_analysis': report.detailed_analysis,
                'recommendations': report.recommendations,
                'implementation_timeframe': report.implementation_timeframe,
                'estimated_impact': report.estimated_impact,
                'generation_method': report.generation_method,
                'metrics_data': {
                    'timestamp': report.metrics.timestamp,
                    'cpu_usage': report.metrics.cpu_usage,
                    'memory_usage': report.metrics.memory_usage,
                    'latency_ms': report.metrics.latency_ms,
                    'disk_usage': report.metrics.disk_usage,
                    'network_in_kbps': report.metrics.network_in_kbps,
                    'network_out_kbps': report.metrics.network_out_kbps,
                    'io_wait': report.metrics.io_wait,
                    'thread_count': report.metrics.thread_count,
                    'active_connections': report.metrics.active_connections,
                    'error_rate': report.metrics.error_rate,
                    'uptime_seconds': report.metrics.uptime_seconds,
                    'temperature_celsius': report.metrics.temperature_celsius,
                    'power_consumption_watts': report.metrics.power_consumption_watts,
                    'service_status': report.metrics.service_status
                }
            }
            
            return APIResponse.success(
                message="Rapport récupéré avec succès",
                data=response_data
            )
            
        except RecommendationReport.DoesNotExist:
            return APIResponse.not_found("Rapport", str(report_id))
        except Exception as e:
            return APIResponse.handle_exception(e, f"Erreur récupération rapport {report_id}")


class RecommendationListView(APIView):
    """
    Vue pour lister tous les rapports de recommandations avec filtres optionnels.
    """
    
    @RecommendationSwaggerSchemas.get_reports_list_schema()
    def get(self, request):
        """
        Récupère la liste des rapports de recommandations avec filtres optionnels.
        """
        try:
            # Application des filtres
            queryset = RecommendationFilters.get_filtered_reports(request.query_params)
            
            # Construction de la réponse
            reports_list = []
            for report in queryset:
                report_data = {
                    'report_id': report.id,
                    'metrics_id': report.metrics.id,
                    'generated_at': report.generated_at,
                    'priority_level': report.priority_level,
                    'is_urgent': report.is_urgent,
                    'executive_summary': report.executive_summary[:200] + "..." if len(report.executive_summary) > 200 else report.executive_summary,
                    'recommendations_count': len(report.recommendations) if report.recommendations else 0,
                    'generation_method': report.generation_method,
                    'implementation_timeframe': report.implementation_timeframe,
                    'estimated_impact': report.estimated_impact,
                    'metrics_timestamp': report.metrics.timestamp
                }
                reports_list.append(report_data)
            
            # Statistiques globales
            from django.utils import timezone
            from datetime import timedelta
            
            total_reports = RecommendationReport.objects.count()
            urgent_count = RecommendationReport.objects.filter(priority_level__in=['high', 'critical']).count()
            recent_count = RecommendationReport.objects.filter(
                generated_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Informations sur les filtres appliqués
            filter_info = RecommendationFilters.get_filter_info(request.query_params)
            limit = int(request.query_params.get('limit', 50))
            
            response_data = {
                'reports': reports_list,
                'pagination': {
                    'returned_count': len(reports_list),
                    'requested_limit': limit,
                    'has_more': len(reports_list) == limit
                },
                'statistics': {
                    'total_reports_all_time': total_reports,
                    'urgent_reports_all_time': urgent_count,
                    'recent_reports_24h': recent_count
                },
                'filters_applied': filter_info
            }
            
            return APIResponse.success(
                message=f"{len(reports_list)} rapports récupérés",
                data=response_data
            )
            
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur récupération liste rapports")


