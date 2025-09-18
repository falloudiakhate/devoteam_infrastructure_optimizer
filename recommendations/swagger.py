"""
Schémas Swagger pour l'application de recommandations.
Centralise les définitions drf-yasg pour une documentation API cohérente.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class RecommendationSwaggerSchemas:
    """
    Schémas Swagger réutilisables pour l'API de recommandations.
    """
    
    # Paramètres communs
    METRICS_ID_PARAM = openapi.Parameter(
        'metrics_id',
        openapi.IN_QUERY,
        description='ID de la métrique pour générer des recommandations spécifiques',
        type=openapi.TYPE_INTEGER,
        required=False
    )
    
    METHOD_PARAM = openapi.Parameter(
        'method',
        openapi.IN_QUERY,
        description='Méthode de génération: classic ou llm',
        type=openapi.TYPE_STRING,
        enum=['classic', 'llm'],
        default='classic',
        required=False
    )
    
    # Réponses communes
    SUCCESS_RESPONSE = {
        200: openapi.Response(
            description='Succès',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'code': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )
    }
    
    ERROR_RESPONSE = {
        400: openapi.Response(
            description='Erreur de validation',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'error_code': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        404: openapi.Response(
            description='Ressource non trouvée',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'error_code': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        500: openapi.Response(
            description='Erreur serveur',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'error_code': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )
    }
    
    @classmethod
    def get_generate_schema(cls):
        """Schéma pour l'endpoint de génération de recommandations."""
        return swagger_auto_schema(
            operation_description=(
                "Génère des recommandations d'optimisation pour une métrique spécifique "
                "ou pour toutes les métriques analysées"
            ),
            operation_summary="Génération de recommandations",
            manual_parameters=[
                cls.METRICS_ID_PARAM,
                cls.METHOD_PARAM
            ],
            responses={
                200: openapi.Response(
                    description='Recommandations générées avec succès',
                    schema=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                            'message': openapi.Schema(type=openapi.TYPE_STRING),
                            'metrics_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'report_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'recommendations_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'priority_level': openapi.Schema(type=openapi.TYPE_STRING),
                            'is_urgent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'processing_time': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'method_used': openapi.Schema(type=openapi.TYPE_STRING),
                            'method_info': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    )
                ),
                **cls.ERROR_RESPONSE
            },
            tags=['Recommandations']
        )
    
    @classmethod
    def get_result_schema(cls):
        """Schéma pour récupérer un rapport de recommandations."""
        return swagger_auto_schema(
            operation_description="Récupère un rapport de recommandations existant par son ID",
            operation_summary="Récupération d'un rapport",
            responses={
                200: openapi.Response(
                    description='Rapport récupéré avec succès',
                    schema=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                            'report_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'metrics_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'generated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'priority_level': openapi.Schema(type=openapi.TYPE_STRING),
                            'is_urgent': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'executive_summary': openapi.Schema(type=openapi.TYPE_STRING),
                            'recommendations': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            ),
                            'implementation_timeframe': openapi.Schema(type=openapi.TYPE_STRING),
                            'generation_method': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                ),
                **cls.ERROR_RESPONSE
            },
            tags=['Recommandations']
        )
    
    @classmethod
    def get_reports_list_schema(cls):
        """Schéma pour lister les rapports de recommandations."""
        return swagger_auto_schema(
            operation_description="Liste tous les rapports de recommandations avec filtres optionnels",
            operation_summary="Liste des rapports",
            manual_parameters=[
                openapi.Parameter(
                    'priority',
                    openapi.IN_QUERY,
                    description='Filtrer par niveau de priorité',
                    type=openapi.TYPE_STRING,
                    enum=['low', 'medium', 'high', 'critical'],
                    required=False
                ),
                openapi.Parameter(
                    'urgent_only',
                    openapi.IN_QUERY,
                    description='Afficher seulement les rapports urgents',
                    type=openapi.TYPE_BOOLEAN,
                    required=False
                ),
                openapi.Parameter(
                    'method',
                    openapi.IN_QUERY,
                    description='Filtrer par méthode de génération',
                    type=openapi.TYPE_STRING,
                    enum=['classic', 'llm'],
                    required=False
                ),
                openapi.Parameter(
                    'limit',
                    openapi.IN_QUERY,
                    description='Nombre maximum de rapports à retourner',
                    type=openapi.TYPE_INTEGER,
                    default=50,
                    required=False
                )
            ],
            responses={
                200: openapi.Response(
                    description='Liste récupérée avec succès',
                    schema=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                            'reports': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            ),
                            'pagination': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'statistics': openapi.Schema(type=openapi.TYPE_OBJECT),
                            'filters_applied': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    )
                ),
                **cls.ERROR_RESPONSE
            },
            tags=['Recommandations']
        )