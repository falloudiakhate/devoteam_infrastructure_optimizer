"""
Codes de réponse et messages pour l'API d'ingestion.
Centralise la gestion des codes d'erreur et des messages de réponse.
"""

from rest_framework import status
from rest_framework.response import Response
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResponseCodes:
    """
    Codes d'erreur personnalisés pour l'API d'ingestion.
    """
    
    # Codes de succès
    SUCCESS = "SUCCESS"
    INGESTION_SUCCESS = "INGESTION_SUCCESS"
    BATCH_INGESTION_SUCCESS = "BATCH_INGESTION_SUCCESS"
    
    # Codes d'erreur - Validation
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"
    INVALID_METRICS_DATA = "INVALID_METRICS_DATA"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    EMPTY_DATA = "EMPTY_DATA"
    
    # Codes d'erreur - Ingestion
    INGESTION_FAILED = "INGESTION_FAILED"
    BATCH_INGESTION_FAILED = "BATCH_INGESTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PARTIAL_INGESTION = "PARTIAL_INGESTION"
    
    # Codes d'erreur - Système
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ResponseMessages:
    """
    Messages standardisés pour les réponses API.
    """
    
    # Messages de succès
    INGESTION_SUCCESS = "Données ingérées avec succès"
    BATCH_INGESTION_SUCCESS = "Ingestion en lot terminée"
    SINGLE_METRIC_INGESTED = "Métrique ingérée avec succès"
    
    # Messages d'erreur - Validation
    INVALID_DATA_FORMAT_MSG = "Format de données invalide"
    INVALID_METRICS_DATA_MSG = "Données de métriques invalides"
    INVALID_TIMESTAMP_MSG = "Format de timestamp invalide"
    MISSING_REQUIRED_FIELDS_MSG = "Champs obligatoires manquants"
    EMPTY_DATA_MSG = "Aucune donnée à ingérer"
    ARRAY_REQUIRED_MSG = "Les données doivent être un tableau"
    
    # Messages d'erreur - Ingestion
    INGESTION_FAILED_MSG = "Erreur lors de l'ingestion des données"
    BATCH_INGESTION_FAILED_MSG = "Erreur lors de l'ingestion en lot"
    VALIDATION_FAILED_MSG = "Validation des données échouée"
    NO_VALID_DATA_MSG = "Aucune donnée valide à ingérer"
    
    # Messages d'erreur - Système
    INTERNAL_ERROR_MSG = "Erreur interne du serveur"
    UNEXPECTED_ERROR_MSG = "Erreur inattendue"
    SERVICE_UNAVAILABLE_MSG = "Service d'ingestion temporairement indisponible"


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
        field_errors: Optional[Dict[str, str]] = None,
        validation_errors: Optional[list] = None
    ) -> Response:
        """
        Crée une réponse d'erreur de validation.
        
        Args:
            message: Message d'erreur principal
            field_errors: Erreurs spécifiques par champ
            validation_errors: Liste des erreurs de validation
            
        Returns:
            Response formatée
        """
        details = {}
        if field_errors:
            details['field_errors'] = field_errors
        if validation_errors:
            details['validation_errors'] = validation_errors
            
        return APIResponse.error(
            message=message,
            code=ResponseCodes.VALIDATION_FAILED,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def ingestion_success(
        metrics_id: int,
        timestamp: str,
        processing_time: float,
        auto_analysis: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Crée une réponse de succès spécifique pour l'ingestion unitaire.
        
        Args:
            metrics_id: ID de la métrique créée
            timestamp: Timestamp de la métrique
            processing_time: Temps de traitement
            auto_analysis: Résultats de l'analyse automatique
            
        Returns:
            Response formatée
        """
        data = {
            'metrics_id': metrics_id,
            'timestamp': timestamp,
            'processing_duration_seconds': round(processing_time, 3)
        }
        
        if auto_analysis:
            data['auto_analysis'] = auto_analysis
        
        return APIResponse.success(
            message=ResponseMessages.SINGLE_METRIC_INGESTED,
            data=data,
            code=ResponseCodes.INGESTION_SUCCESS,
            status_code=status.HTTP_201_CREATED
        )
    
    @staticmethod
    def batch_ingestion_success(
        total: int,
        ingested: int,
        errors: int,
        processing_time: float,
        metrics_ids: list,
        validation_errors: Optional[list] = None,
        auto_analysis: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Crée une réponse de succès spécifique pour l'ingestion en lot.
        
        Args:
            total: Nombre total de métriques
            ingested: Nombre de métriques ingérées
            errors: Nombre d'erreurs
            processing_time: Temps de traitement total
            metrics_ids: IDs des métriques créées
            validation_errors: Erreurs de validation
            auto_analysis: Résultats de l'analyse automatique
            
        Returns:
            Response formatée
        """
        data = {
            'total': total,
            'ingested': ingested,
            'errors': errors,
            'processing_duration_seconds': round(processing_time, 3),
            'average_processing_time_ms': round((processing_time / max(total, 1)) * 1000, 2),
            'metrics_ids': metrics_ids
        }
        
        if validation_errors:
            # Limiter les erreurs affichées pour éviter la surcharge
            data['validation_errors'] = validation_errors[:10] if len(validation_errors) > 10 else validation_errors
            if len(validation_errors) > 10:
                data['validation_errors_truncated'] = len(validation_errors) - 10
        
        if auto_analysis:
            data['auto_analysis'] = auto_analysis
        
        # Déterminer le message et le code basé sur les résultats
        if errors == 0:
            message = f"Ingestion réussie: {ingested}/{total} métriques traitées avec succès"
            code = ResponseCodes.BATCH_INGESTION_SUCCESS
        elif ingested == 0:
            message = f"Ingestion échouée: {errors}/{total} erreurs, aucune métrique ingérée"
            code = ResponseCodes.BATCH_INGESTION_FAILED
        else:
            message = f"Ingestion partielle: {ingested}/{total} métriques ingérées, {errors} erreurs"
            code = ResponseCodes.PARTIAL_INGESTION
        
        data['message'] = message
        
        status_code = status.HTTP_201_CREATED if ingested > 0 else status.HTTP_400_BAD_REQUEST
        
        return APIResponse.success(
            message=message,
            data=data,
            code=code,
            status_code=status_code
        )
    
    @staticmethod
    def invalid_data_format(received_type: str = None) -> Response:
        """
        Crée une réponse pour un format de données invalide.
        
        Args:
            received_type: Type de données reçu
            
        Returns:
            Response formatée
        """
        details = {}
        if received_type:
            details['received_type'] = received_type
            
        return APIResponse.error(
            message=ResponseMessages.INVALID_DATA_FORMAT_MSG,
            code=ResponseCodes.INVALID_DATA_FORMAT,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def empty_data() -> Response:
        """
        Crée une réponse pour des données vides.
        
        Returns:
            Response formatée
        """
        return APIResponse.error(
            message=ResponseMessages.EMPTY_DATA_MSG,
            code=ResponseCodes.EMPTY_DATA,
            status_code=status.HTTP_400_BAD_REQUEST
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