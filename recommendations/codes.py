"""
Codes de réponse et messages pour l'API de recommandations.
Centralise la gestion des codes d'erreur et des messages de réponse.
"""

from rest_framework import status
from rest_framework.response import Response
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ResponseCodes:
    """
    Codes d'erreur personnalisés pour l'API de recommandations.
    """
    
    # Codes de succès
    SUCCESS = "SUCCESS"
    RECOMMENDATIONS_GENERATED = "RECOMMENDATIONS_GENERATED"
    REPORT_ALREADY_EXISTS = "REPORT_ALREADY_EXISTS"
    
    # Codes d'erreur - Validation
    INVALID_METRICS_ID = "INVALID_METRICS_ID"
    INVALID_REPORT_ID = "INVALID_REPORT_ID"
    INVALID_METHOD = "INVALID_METHOD"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    
    # Codes d'erreur - Données
    METRICS_NOT_FOUND = "METRICS_NOT_FOUND"
    REPORT_NOT_FOUND = "REPORT_NOT_FOUND"
    NO_METRICS_FOR_RECOMMENDATIONS = "NO_METRICS_FOR_RECOMMENDATIONS"
    METRICS_NOT_ANALYZED = "METRICS_NOT_ANALYZED"
    
    # Codes d'erreur - Traitement
    GENERATION_FAILED = "GENERATION_FAILED"
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
    GENERATION_SUCCESS = "Recommandations générées avec succès"
    REPORT_ALREADY_EXISTS_MSG = "Ce rapport de recommandations existe déjà"
    BATCH_GENERATION_SUCCESS = "Génération en lot terminée"
    NO_METRICS_PENDING = "Aucune métrique en attente de recommandations"
    
    # Messages d'erreur - Validation
    INVALID_METRICS_ID_MSG = "L'ID de la métrique n'est pas valide"
    INVALID_REPORT_ID_MSG = "L'ID du rapport n'est pas valide"
    INVALID_METHOD_MSG = "La méthode de génération spécifiée n'est pas valide"
    MISSING_PARAMETERS_MSG = "Paramètres requis manquants"
    
    # Messages d'erreur - Données
    METRICS_NOT_FOUND_MSG = "Métrique non trouvée"
    REPORT_NOT_FOUND_MSG = "Rapport de recommandations non trouvé"
    METRICS_NOT_ANALYZED_MSG = "La métrique doit être analysée avant génération de recommandations"
    
    # Messages d'erreur - Traitement
    GENERATION_FAILED_MSG = "Erreur lors de la génération des recommandations"
    SERVICE_UNAVAILABLE_MSG = "Service de génération temporairement indisponible"
    LLM_NOT_CONFIGURED_MSG = "Génération LLM non configurée, utilisez la méthode 'classic'"
    
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
            resource_type: Type de ressource (ex: "Métrique", "Rapport")
            resource_id: ID de la ressource si disponible
            
        Returns:
            Response formatée
        """
        if resource_type.lower() == "métrique":
            message = ResponseMessages.METRICS_NOT_FOUND_MSG
            code = ResponseCodes.METRICS_NOT_FOUND
        elif resource_type.lower() == "rapport":
            message = ResponseMessages.REPORT_NOT_FOUND_MSG
            code = ResponseCodes.REPORT_NOT_FOUND
        else:
            message = f"{resource_type} non trouvée"
            code = ResponseCodes.REPORT_NOT_FOUND
            
        if resource_id:
            message += f" (ID: {resource_id})"
            
        return APIResponse.error(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def generation_success(
        metrics_id: int,
        report_id: int,
        recommendations_count: int,
        priority_level: str,
        is_urgent: bool,
        processing_time: float,
        method_used: str,
        method_info: Dict[str, Any]
    ) -> Response:
        """
        Crée une réponse de succès spécifique pour la génération de recommandations.
        
        Args:
            metrics_id: ID de la métrique analysée
            report_id: ID du rapport créé
            recommendations_count: Nombre de recommandations générées
            priority_level: Niveau de priorité
            is_urgent: Si le rapport est urgent
            processing_time: Temps de traitement
            method_used: Méthode utilisée
            method_info: Informations sur la méthode
            
        Returns:
            Response formatée
        """
        data = {
            'metrics_id': metrics_id,
            'report_id': report_id,
            'recommendations_count': recommendations_count,
            'priority_level': priority_level,
            'is_urgent': is_urgent,
            'processing_duration_seconds': round(processing_time, 3),
            'method_used': method_used,
            'method_info': method_info
        }
        
        return APIResponse.success(
            message=ResponseMessages.GENERATION_SUCCESS,
            data=data,
            code=ResponseCodes.RECOMMENDATIONS_GENERATED,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def report_already_exists(
        metrics_id: int,
        report_id: Optional[int] = None,
        report = None
    ) -> Response:
        """
        Crée une réponse pour un rapport déjà existant avec les détails.
        
        Args:
            metrics_id: ID de la métrique
            report_id: ID du rapport existant
            report: Instance du rapport existant
            
        Returns:
            Response formatée
        """
        data = {
            'metrics_id': metrics_id,
            'report_id': report_id
        }
        
        # Ajouter les détails du rapport si disponibles
        if report:
            data.update({
                'recommendations_count': len(report.recommendations) if hasattr(report, 'recommendations') else 0,
                'priority_level': report.priority_level,
                'is_urgent': report.is_urgent,
                'generated_at': report.generated_at,
                'generation_method': report.generation_method,
                'executive_summary': report.executive_summary[:200] + "..." if len(report.executive_summary) > 200 else report.executive_summary
            })
        
        return APIResponse.success(
            message=ResponseMessages.REPORT_ALREADY_EXISTS_MSG,
            data=data,
            code=ResponseCodes.REPORT_ALREADY_EXISTS,
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