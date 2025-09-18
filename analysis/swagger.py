"""
Schémas Swagger pour l'API d'analyse des anomalies.
Centralise toutes les définitions de documentation API.
"""

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class AnalysisSwaggerSchemas:
    """
    Classe contenant tous les schémas Swagger pour l'analyse.
    """
    
    # Paramètres communs
    METRICS_ID_PARAM = openapi.Parameter(
        'metrics_id',
        openapi.IN_QUERY,
        description="ID de la métrique à analyser (optionnel, si non fourni analyse toutes les métriques non analysées)",
        type=openapi.TYPE_INTEGER
    )
    
    METHOD_PARAM = openapi.Parameter(
        'method',
        openapi.IN_QUERY,
        description="Méthode d'analyse: 'classic' ou 'llm' (défaut: classic)",
        type=openapi.TYPE_STRING,
        enum=['classic', 'llm']
    )
    
    LIMIT_PARAM = openapi.Parameter(
        'limit',
        openapi.IN_QUERY,
        description="Nombre maximum d'anomalies à retourner (défaut: 50)",
        type=openapi.TYPE_INTEGER
    )
    
    CRITICAL_ONLY_PARAM = openapi.Parameter(
        'critical_only',
        openapi.IN_QUERY,
        description="Ne retourner que les anomalies critiques (score >= 7)",
        type=openapi.TYPE_BOOLEAN
    )
    
    HOURS_PARAM = openapi.Parameter(
        'hours',
        openapi.IN_QUERY,
        description="Période en heures pour filtrer les anomalies récentes",
        type=openapi.TYPE_INTEGER
    )
    
    MIN_SEVERITY_PARAM = openapi.Parameter(
        'min_severity',
        openapi.IN_QUERY,
        description="Score de sévérité minimum (1-10)",
        type=openapi.TYPE_INTEGER
    )
    
    # Schémas de réponse
    ANALYSIS_SUCCESS_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'metrics_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'analysis_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'anomalies_detected': openapi.Schema(type=openapi.TYPE_INTEGER),
            'severity_score': openapi.Schema(type=openapi.TYPE_INTEGER),
            'is_critical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'anomaly_summary': openapi.Schema(type=openapi.TYPE_STRING),
            'processing_duration_seconds': openapi.Schema(type=openapi.TYPE_NUMBER),
            'method_used': openapi.Schema(type=openapi.TYPE_STRING),
            'method_info': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'current_method': openapi.Schema(type=openapi.TYPE_STRING),
                    'detector_class': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        }
    )
    
    ERROR_RESPONSE = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'error': openapi.Schema(type=openapi.TYPE_STRING),
            'error_code': openapi.Schema(type=openapi.TYPE_STRING),
            'details': openapi.Schema(type=openapi.TYPE_OBJECT)
        }
    )

    @staticmethod
    def get_analyze_schema():
        """Retourne le schéma pour l'endpoint d'analyse."""
        return swagger_auto_schema(
            operation_description="Lance l'analyse d'anomalies pour une métrique spécifique ou toutes les métriques non analysées",
            manual_parameters=[
                AnalysisSwaggerSchemas.METRICS_ID_PARAM,
                AnalysisSwaggerSchemas.METHOD_PARAM
            ],
            responses={
                200: AnalysisSwaggerSchemas.ANALYSIS_SUCCESS_RESPONSE,
                400: AnalysisSwaggerSchemas.ERROR_RESPONSE,
                404: AnalysisSwaggerSchemas.ERROR_RESPONSE,
                500: AnalysisSwaggerSchemas.ERROR_RESPONSE
            }
        )
    
    @staticmethod
    def get_result_schema():
        """Retourne le schéma pour l'endpoint de résultat."""
        return swagger_auto_schema(
            operation_description="Récupère les résultats d'une analyse d'anomalies par son ID",
            responses={
                200: openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'analysis_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'metrics_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'detected_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                        'anomalies_detected': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'severity_score': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_critical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'anomaly_summary': openapi.Schema(type=openapi.TYPE_STRING),
                        'anomaly_details': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'metrics_data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                ),
                404: AnalysisSwaggerSchemas.ERROR_RESPONSE,
                500: AnalysisSwaggerSchemas.ERROR_RESPONSE
            }
        )
    
    @staticmethod
    def get_anomalies_list_schema():
        """Retourne le schéma pour l'endpoint de liste des anomalies."""
        return swagger_auto_schema(
            operation_description="Récupère la liste de toutes les anomalies détectées",
            manual_parameters=[
                AnalysisSwaggerSchemas.LIMIT_PARAM,
                AnalysisSwaggerSchemas.CRITICAL_ONLY_PARAM,
                AnalysisSwaggerSchemas.HOURS_PARAM,
                AnalysisSwaggerSchemas.MIN_SEVERITY_PARAM
            ],
            responses={
                200: openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'anomalies': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'analysis_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'metrics_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'detected_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                                    'anomalies_detected': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'severity_score': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'is_critical': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'anomaly_summary': openapi.Schema(type=openapi.TYPE_STRING),
                                    'anomaly_types': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING)
                                    ),
                                    'metrics_timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
                                }
                            )
                        ),
                        'pagination': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'statistics': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'filters_applied': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                ),
                500: AnalysisSwaggerSchemas.ERROR_RESPONSE
            }
        )