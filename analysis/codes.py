"""
Codes de réponse et messages pour l'API d'analyse des anomalies.
Centralise la gestion des codes d'erreur et des messages de réponse.
"""

from rest_framework import status
from rest_framework.response import Response
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResponseCodes:
    """
    Codes d'erreur personnalisés pour l'API d'analyse.
    """
    
    # Codes de succès
    SUCCESS = "SUCCESS"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    ANALYSIS_ALREADY_EXISTS = "ANALYSIS_ALREADY_EXISTS"
    
    # Codes d'erreur - Validation
    INVALID_METRICS_ID = "INVALID_METRICS_ID"
    INVALID_ANALYSIS_ID = "INVALID_ANALYSIS_ID"
    INVALID_METHOD = "INVALID_METHOD"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    
    # Codes d'erreur - Données
    METRICS_NOT_FOUND = "METRICS_NOT_FOUND"
    ANALYSIS_NOT_FOUND = "ANALYSIS_NOT_FOUND"
    NO_METRICS_TO_ANALYZE = "NO_METRICS_TO_ANALYZE"
    
    # Codes d'erreur - Traitement
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    LLM_NOT_CONFIGURED = "LLM_NOT_CONFIGURED"
    
    # Codes d'erreur - Système
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class ResponseMessages:
    """
    Messages standardisés pour les réponses API.
    """
    
    # Messages de succès
    ANALYSIS_SUCCESS = "Analyse terminée avec succès"
    ANALYSIS_ALREADY_DONE = "Cette métrique a déjà été analysée"
    BATCH_ANALYSIS_SUCCESS = "Analyse en lot terminée"
    NO_METRICS_PENDING = "Aucune métrique en attente d'analyse"
    
    # Messages d'erreur - Validation
    INVALID_METRICS_ID_MSG = "L'ID de la métrique n'est pas valide"
    INVALID_ANALYSIS_ID_MSG = "L'ID de l'analyse n'est pas valide"
    INVALID_METHOD_MSG = "La méthode d'analyse spécifiée n'est pas valide"
    MISSING_PARAMETERS_MSG = "Paramètres requis manquants"
    
    # Messages d'erreur - Données
    METRICS_NOT_FOUND_MSG = "Métrique non trouvée"
    ANALYSIS_NOT_FOUND_MSG = "Analyse non trouvée"
    
    # Messages d'erreur - Traitement
    ANALYSIS_FAILED_MSG = "Erreur lors de l'analyse des métriques"
    SERVICE_UNAVAILABLE_MSG = "Service d'analyse temporairement indisponible"
    LLM_NOT_CONFIGURED_MSG = "Analyse LLM non configurée, utilisez la méthode 'classic'"
    
    # Messages d'erreur - Système
    INTERNAL_ERROR_MSG = "Erreur interne du serveur"
    UNEXPECTED_ERROR_MSG = "Erreur inattendue"


class APIResponse:
    """
    Classe utilitaire pour créer des réponses API standardisées.
    """
    
    @staticmethod
    def success(
        message: str,
        data: Optional[Dict[str, Any]] = None,
        code: str = ResponseCodes.SUCCESS,
        status_code: int = status.HTTP_200_OK
    ) -> Response:
        """
        Crée une réponse de succès standardisée.
        
        Args:
            message: Message de succès
            data: Données à inclure dans la réponse
            code: Code de réponse personnalisé
            status_code: Code de statut HTTP
            
        Returns:
            Response formatée
        """
        response_data = {
            'success': True,
            'message': message,
            'code': code
        }
        
        if data:
            response_data.update(data)
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(
        message: str,
        code: str = ResponseCodes.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> Response:
        """
        Crée une réponse d'erreur standardisée.
        
        Args:
            message: Message d'erreur
            code: Code d'erreur personnalisé
            details: Détails supplémentaires sur l'erreur
            status_code: Code de statut HTTP
            
        Returns:
            Response formatée
        """
        response_data = {
            'success': False,
            'error': message,
            'error_code': code
        }
        
        if details:
            response_data['details'] = details
            
        # Log de l'erreur
        logger.error(f"API Error - Code: {code}, Message: {message}, Details: {details}")
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def validation_error(
        message: str,
        field_errors: Optional[Dict[str, str]] = None
    ) -> Response:
        """
        Crée une réponse d'erreur de validation.
        
        Args:
            message: Message d'erreur principal
            field_errors: Erreurs spécifiques par champ
            
        Returns:
            Response formatée
        """
        details = {}
        if field_errors:
            details['field_errors'] = field_errors
            
        return APIResponse.error(
            message=message,
            code=ResponseCodes.INVALID_PARAMETERS,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def not_found(
        resource_type: str = "Ressource",
        resource_id: Optional[str] = None
    ) -> Response:
        """
        Crée une réponse pour une ressource non trouvée.
        
        Args:
            resource_type: Type de ressource (ex: "Métrique", "Analyse")
            resource_id: ID de la ressource si disponible
            
        Returns:
            Response formatée
        """
        if resource_type.lower() == "métrique":
            message = ResponseMessages.METRICS_NOT_FOUND_MSG
            code = ResponseCodes.METRICS_NOT_FOUND
        elif resource_type.lower() == "analyse":
            message = ResponseMessages.ANALYSIS_NOT_FOUND_MSG
            code = ResponseCodes.ANALYSIS_NOT_FOUND
        else:
            message = f"{resource_type} non trouvée"
            code = ResponseCodes.ANALYSIS_NOT_FOUND
            
        if resource_id:
            message += f" (ID: {resource_id})"
            
        return APIResponse.error(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def analysis_success(
        metrics_id: int,
        analysis_id: int,
        anomalies_detected: int,
        severity_score: int,
        is_critical: bool,
        anomaly_summary: str,
        processing_time: float,
        method_used: str,
        method_info: Dict[str, Any]
    ) -> Response:
        """
        Crée une réponse de succès spécifique pour l'analyse.
        
        Args:
            metrics_id: ID de la métrique analysée
            analysis_id: ID de l'analyse créée
            anomalies_detected: Nombre d'anomalies détectées
            severity_score: Score de sévérité
            is_critical: Si l'anomalie est critique
            anomaly_summary: Résumé des anomalies
            processing_time: Temps de traitement
            method_used: Méthode utilisée
            method_info: Informations sur la méthode
            
        Returns:
            Response formatée
        """
        data = {
            'metrics_id': metrics_id,
            'analysis_id': analysis_id,
            'anomalies_detected': anomalies_detected,
            'severity_score': severity_score,
            'is_critical': is_critical,
            'anomaly_summary': anomaly_summary,
            'processing_duration_seconds': round(processing_time, 3),
            'method_used': method_used,
            'method_info': method_info
        }
        
        return APIResponse.success(
            message=ResponseMessages.ANALYSIS_SUCCESS,
            data=data,
            code=ResponseCodes.ANALYSIS_COMPLETED,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def analysis_already_exists(
        metrics_id: int,
        analysis_id: Optional[int] = None,
        anomaly_detection = None
    ) -> Response:
        """
        Crée une réponse pour une analyse déjà existante avec les détails.
        
        Args:
            metrics_id: ID de la métrique
            analysis_id: ID de l'analyse existante
            anomaly_detection: Instance de l'analyse existante
            
        Returns:
            Response formatée
        """
        data = {
            'metrics_id': metrics_id,
            'analysis_id': analysis_id
        }
        
        # Ajouter les détails de l'analyse si disponibles
        if anomaly_detection:
            data.update({
                'anomalies_detected': anomaly_detection.total_anomalies,
                'severity_score': anomaly_detection.severity_score,
                'is_critical': anomaly_detection.is_critical,
                'anomaly_summary': anomaly_detection.anomaly_summary,
                'detected_at': anomaly_detection.detected_at,
                'analysis_method': anomaly_detection.analysis_method,
                'analysis_details': {
                    'cpu_anomaly': anomaly_detection.cpu_anomaly,
                    'memory_anomaly': anomaly_detection.memory_anomaly,
                    'latency_anomaly': anomaly_detection.latency_anomaly,
                    'disk_anomaly': anomaly_detection.disk_anomaly,
                    'io_anomaly': anomaly_detection.io_anomaly,
                    'error_rate_anomaly': anomaly_detection.error_rate_anomaly,
                    'temperature_anomaly': anomaly_detection.temperature_anomaly,
                    'power_anomaly': anomaly_detection.power_anomaly,
                    'service_anomaly': anomaly_detection.service_anomaly
                }
            })
        
        return APIResponse.success(
            message=ResponseMessages.ANALYSIS_ALREADY_DONE,
            data=data,
            code=ResponseCodes.ANALYSIS_ALREADY_EXISTS,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def handle_exception(exception: Exception, context: str = "") -> Response:
        """
        Gère une exception et retourne une réponse d'erreur appropriée.
        
        Args:
            exception: Exception capturée
            context: Contexte de l'erreur
            
        Returns:
            Response formatée
        """
        error_message = f"{ResponseMessages.UNEXPECTED_ERROR_MSG}: {str(exception)}"
        
        if context:
            error_message = f"{context} - {error_message}"
            
        return APIResponse.error(
            message=error_message,
            code=ResponseCodes.INTERNAL_ERROR,
            details={'exception_type': type(exception).__name__},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )