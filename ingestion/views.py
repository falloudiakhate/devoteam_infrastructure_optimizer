import time
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import InfrastructureMetrics
from .services import DataIngestionService
from .serializers import MetricsIngestionSerializer
from .codes import APIResponse, ResponseCodes, ResponseMessages
from .swagger import IngestionSwaggerSchemas
from .filters import ValidationFilters
from analysis.services import AnomalyDetectionService
from recommendations.services import RecommendationService

logger = logging.getLogger(__name__)


class DataIngestionView(APIView):
    """
    Vue pour l'ingestion des données de métriques.
    Supporte l'ingestion unitaire et en lot.
    """
    
    @IngestionSwaggerSchemas.get_data_ingestion_schema()
    def post(self, request):
        """
        Ingère des données de métriques (unitaire ou lot).
        """
        try:
            start_time = time.time()
            data = request.data
            
            if not data:
                return APIResponse.empty_data()
            
            # Détection du type de données (objet unique ou liste)
            if isinstance(data, list):
                return self._handle_batch_ingestion(data, start_time)
            else:
                return self._handle_single_ingestion(data, start_time, request)
                
        except Exception as e:
            logger.error(f"Erreur ingestion données: {e}")
            return APIResponse.handle_exception(e, "Erreur ingestion données")
    
    def _handle_single_ingestion(self, data, start_time, request):
        """Gère l'ingestion d'une métrique unique."""
        serializer = MetricsIngestionSerializer(data=data)
        
        if not serializer.is_valid():
            return APIResponse.validation_error(
                ResponseMessages.VALIDATION_FAILED_MSG,
                field_errors=serializer.errors
            )
        
        # Ingestion via le service
        ingestion_service = DataIngestionService()
        metrics = ingestion_service.ingest_metrics_data(serializer.validated_data)
        
        if not metrics:
            return APIResponse.error(
                ResponseMessages.INGESTION_FAILED_MSG,
                ResponseCodes.INGESTION_FAILED
            )
        
        processing_time = time.time() - start_time
        
        # Lancement automatique de l'analyse si demandé
        auto_analysis = None
        auto_analyze = request.query_params.get('auto_analyze', 'false').lower() == 'true'
        if auto_analyze:
            auto_analysis = self._perform_auto_analysis(metrics)
        
        return APIResponse.ingestion_success(
            metrics_id=metrics.id,
            timestamp=str(metrics.timestamp),
            processing_time=processing_time,
            auto_analysis=auto_analysis
        )
    
    def _handle_batch_ingestion(self, data_list, start_time):
        """Gère l'ingestion en lot."""
        if not data_list:
            return APIResponse.empty_data()
        
        # Validation des données
        valid_data = []
        validation_errors = []
        
        for i, item in enumerate(data_list):
            serializer = MetricsIngestionSerializer(data=item)
            if serializer.is_valid():
                valid_data.append(serializer.validated_data)
            else:
                validation_errors.append(f"Ligne {i+1}: {serializer.errors}")
        
        if not valid_data:
            return APIResponse.validation_error(
                ResponseMessages.NO_VALID_DATA_MSG,
                validation_errors=validation_errors
            )
        
        # Ingestion en lot
        ingestion_service = DataIngestionService()
        results = ingestion_service.ingest_batch_metrics(valid_data)
        
        processing_time = time.time() - start_time
        
        return APIResponse.batch_ingestion_success(
            total=len(data_list),
            ingested=results['success'],
            errors=results['errors'],
            processing_time=processing_time,
            metrics_ids=results.get('metrics_ids', []),
            validation_errors=validation_errors
        )
    
    def _perform_auto_analysis(self, metrics):
        """Lance automatiquement l'analyse et les recommandations."""
        try:
            # Analyse des anomalies
            anomaly_service = AnomalyDetectionService()
            anomaly_detection = anomaly_service.analyze_metrics(metrics)
            
            # Génération des recommandations
            if anomaly_detection:
                recommendation_service = RecommendationService()
                report = recommendation_service.generate_recommendation_report(metrics)
                
                if report:
                    return {
                        'analysis_completed': True,
                        'anomalies_detected': anomaly_detection.total_anomalies,
                        'severity_score': anomaly_detection.severity_score,
                        'recommendations_generated': True,
                        'priority_level': report.priority_level
                    }
                else:
                    return {
                        'analysis_completed': True,
                        'recommendations_generated': False
                    }
            else:
                return {
                    'analysis_completed': False
                }
                
        except Exception as e:
            logger.error(f"Erreur auto-analyse: {e}")
            return {
                'error': f'Erreur auto-analyse: {str(e)}'
            }


class BulkIngestionView(APIView):
    """
    Vue spécialisée pour l'ingestion en lot de métriques.
    Optimisée pour traiter de gros volumes de données.
    """
    
    @IngestionSwaggerSchemas.get_bulk_ingestion_schema()
    def post(self, request):
        """
        Ingère plusieurs métriques en lot.
        
        Prend en charge le traitement par lot avec gestion d'erreurs optimisée.
        """
        try:
            start_time = time.time()
            data = request.data
            
            logger.info(f"Données reçues: type={type(data).__name__}, longueur={len(data) if hasattr(data, '__len__') else 'N/A'}")
            
            # Vérifier que les données sont un tableau
            if not isinstance(data, list):
                logger.warning(f"Type de données incorrect: {type(data).__name__}, contenu: {str(data)[:200]}...")
                return APIResponse.invalid_data_format(received_type=type(data).__name__)
            
            if not data:
                return APIResponse.empty_data()
            
            # Récupération des paramètres
            auto_analyze = request.query_params.get('auto_analyze', 'false').lower() == 'true'
            batch_size = int(request.query_params.get('batch_size', 100))
            continue_on_error = request.query_params.get('continue_on_error', 'true').lower() == 'true'
            
            logger.info(f"Début ingestion en lot: {len(data)} métriques, batch_size={batch_size}")
            
            # Traitement en lot avec gestion d'erreurs améliorée
            result = self._process_bulk_ingestion(
                data, batch_size, continue_on_error, auto_analyze, start_time
            )
            
            # Détermination du code de statut
            if result['ingested'] > 0:
                status_code = status.HTTP_201_CREATED
            elif result['total'] > 0:
                status_code = status.HTTP_400_BAD_REQUEST  # Des données étaient fournies mais toutes invalides
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            return APIResponse.success(
                message=result['message'],
                data={
                    'total': result['total'],
                    'ingested': result['ingested'],
                    'errors': result['errors'],
                    'processing_duration_seconds': result['processing_duration_seconds'],
                    'average_processing_time_ms': result['average_processing_time_ms'],
                    'metrics_ids': result['metrics_ids'],
                    'validation_errors': result.get('validation_errors', []),
                    'auto_analysis': result.get('auto_analysis')
                },
                code=ResponseCodes.BATCH_INGESTION_SUCCESS if result['ingested'] > 0 else ResponseCodes.BATCH_INGESTION_FAILED,
                status_code=status_code
            )
            
        except ValueError as ve:
            logger.error(f"Erreur de validation bulk ingestion: {ve}")
            return APIResponse.error(
                message="Paramètres invalides",
                code=ResponseCodes.INVALID_PARAMETERS,
                details={'validation_error': str(ve)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Erreur bulk ingestion: {e}")
            return APIResponse.handle_exception(e, "Erreur bulk ingestion")
    
    def _process_bulk_ingestion(self, data_list, batch_size, continue_on_error, auto_analyze, start_time):
        """
        Traite l'ingestion en lot avec gestion optimisée des erreurs.
        """
        total = len(data_list)
        ingested = 0
        errors = 0
        validation_errors = []
        metrics_ids = []
        analysis_results = []
        
        # Service d'ingestion
        ingestion_service = DataIngestionService()
        
        # Services pour l'analyse automatique
        if auto_analyze:
            anomaly_service = AnomalyDetectionService()
            recommendation_service = RecommendationService()
        
        # Traitement par lots
        for i in range(0, total, batch_size):
            batch = data_list[i:i + batch_size]
            logger.info(f"Traitement du lot {i//batch_size + 1}: éléments {i} à {i + len(batch) - 1}")
            
            batch_valid_data = []
            batch_errors = []
            
            # Validation du lot
            for j, item in enumerate(batch):
                global_index = i + j
                serializer = MetricsIngestionSerializer(data=item)
                
                if serializer.is_valid():
                    batch_valid_data.append(serializer.validated_data)
                else:
                    error_msg = f"Ligne {global_index + 1}: {serializer.errors}"
                    batch_errors.append(error_msg)
                    validation_errors.append(error_msg)
                    errors += 1
                    
                    if not continue_on_error:
                        logger.error(f"Arrêt du traitement à la ligne {global_index + 1}")
                        break
            
            # Si pas de données valides dans ce lot et qu'on ne continue pas sur erreur
            if not batch_valid_data and not continue_on_error:
                break
            
            # Ingestion du lot valide
            if batch_valid_data:
                try:
                    batch_results = ingestion_service.ingest_batch_metrics(batch_valid_data)
                    batch_ingested = batch_results.get('success', 0)
                    batch_errors_count = batch_results.get('errors', 0)
                    
                    ingested += batch_ingested
                    errors += batch_errors_count
                    
                    # Récupération des IDs des métriques créées
                    if 'metrics_ids' in batch_results:
                        metrics_ids.extend(batch_results['metrics_ids'])
                    
                    # Analyse automatique si demandée
                    if auto_analyze and batch_results.get('metrics_instances'):
                        for metrics in batch_results['metrics_instances']:
                            try:
                                self._perform_auto_analysis(
                                    metrics, anomaly_service, recommendation_service, analysis_results
                                )
                            except Exception as e:
                                logger.error(f"Erreur auto-analyse métrique {metrics.id}: {e}")
                    
                except Exception as e:
                    logger.error(f"Erreur traitement lot: {e}")
                    errors += len(batch_valid_data)
                    if not continue_on_error:
                        break
        
        # Construction du résultat final
        processing_time = time.time() - start_time
        
        result = {
            'success': ingested > 0,
            'message': self._build_result_message(total, ingested, errors),
            'total': total,
            'ingested': ingested,
            'errors': errors,
            'processing_duration_seconds': round(processing_time, 3),
            'average_processing_time_ms': round((processing_time / max(total, 1)) * 1000, 2),
            'metrics_ids': metrics_ids,
            'validation_errors': validation_errors[:10] if len(validation_errors) > 10 else validation_errors  # Limiter les erreurs affichées
        }
        
        # Ajout des résultats d'analyse si applicable
        if auto_analyze and analysis_results:
            result['auto_analysis'] = {
                'total_analyzed': len(analysis_results),
                'anomalies_detected': sum(1 for r in analysis_results if r.get('anomalies_count', 0) > 0),
                'recommendations_generated': sum(1 for r in analysis_results if r.get('recommendations_generated', False)),
                'critical_issues': sum(1 for r in analysis_results if r.get('is_critical', False))
            }
        
        logger.info(f"Ingestion terminée: {ingested}/{total} succès, {errors} erreurs")
        return result
    
    def _perform_auto_analysis(self, metrics, anomaly_service, recommendation_service, analysis_results):
        """Effectue l'analyse automatique pour une métrique."""
        try:
            # Analyse des anomalies
            anomaly_detection = anomaly_service.analyze_metrics(metrics)
            
            analysis_result = {
                'metrics_id': metrics.id,
                'analysis_completed': anomaly_detection is not None
            }
            
            if anomaly_detection:
                analysis_result.update({
                    'anomalies_count': anomaly_detection.total_anomalies,
                    'severity_score': anomaly_detection.severity_score,
                    'is_critical': anomaly_detection.is_critical
                })
                
                # Génération des recommandations
                try:
                    report = recommendation_service.generate_recommendation_report(metrics)
                    analysis_result['recommendations_generated'] = report is not None
                    if report:
                        analysis_result['priority_level'] = report.priority_level
                except Exception as e:
                    logger.error(f"Erreur génération recommandations métrique {metrics.id}: {e}")
                    analysis_result['recommendations_generated'] = False
            
            analysis_results.append(analysis_result)
            
        except Exception as e:
            logger.error(f"Erreur analyse métrique {metrics.id}: {e}")
            analysis_results.append({
                'metrics_id': metrics.id,
                'analysis_completed': False,
                'error': str(e)
            })
    
    def _build_result_message(self, total, ingested, errors):
        """Construit le message de résultat."""
        if errors == 0:
            return f"Ingestion réussie: {ingested}/{total} métriques traitées avec succès"
        elif ingested == 0:
            return f"Ingestion échouée: {errors}/{total} erreurs, aucune métrique ingérée"
        else:
            return f"Ingestion partielle: {ingested}/{total} métriques ingérées, {errors} erreurs"


class MetricsListView(APIView):
    """
    Vue pour récupérer la liste des métriques ingérées.
    """
    
    def get(self, request):
        """
        Récupère la liste des métriques avec filtres optionnels.
        """
        try:
            # Récupération des paramètres de filtrage
            limit = int(request.query_params.get('limit', 50))
            
            # Récupération des métriques
            queryset = InfrastructureMetrics.objects.all()[:limit]
            
            # Construction de la réponse
            metrics_list = []
            for metric in queryset:
                metric_data = {
                    'id': metric.id,
                    'timestamp': metric.timestamp,
                    'cpu_usage': metric.cpu_usage,
                    'memory_usage': metric.memory_usage,
                    'latency_ms': metric.latency_ms,
                    'disk_usage': metric.disk_usage,
                    'network_in_kbps': metric.network_in_kbps,
                    'network_out_kbps': metric.network_out_kbps,
                    'io_wait': metric.io_wait,
                    'thread_count': metric.thread_count,
                    'active_connections': metric.active_connections,
                    'error_rate': metric.error_rate,
                    'uptime_seconds': metric.uptime_seconds,
                    'temperature_celsius': metric.temperature_celsius,
                    'power_consumption_watts': metric.power_consumption_watts,
                    'service_status': metric.service_status,
                    'is_anomalous': metric.is_anomalous,
                    'analysis_completed': metric.analysis_completed,
                    'created_at': metric.created_at
                }
                metrics_list.append(metric_data)
            
            # Statistiques globales
            total_metrics = InfrastructureMetrics.objects.count()
            analyzed_count = InfrastructureMetrics.objects.filter(analysis_completed=True).count()
            anomalous_count = InfrastructureMetrics.objects.filter(is_anomalous=True).count()
            
            response_data = {
                'metrics': metrics_list,
                'pagination': {
                    'returned_count': len(metrics_list),
                    'requested_limit': limit,
                    'has_more': len(metrics_list) == limit
                },
                'statistics': {
                    'total_metrics_all_time': total_metrics,
                    'analyzed_metrics': analyzed_count,
                    'anomalous_metrics': anomalous_count
                }
            }
            
            return APIResponse.success(
                message=f"{len(metrics_list)} métriques récupérées",
                data=response_data
            )
            
        except Exception as e:
            return APIResponse.handle_exception(e, "Erreur récupération liste métriques")


