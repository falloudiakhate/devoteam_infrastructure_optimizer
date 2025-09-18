"""
Schémas Swagger pour l'application d'ingestion.
Centralise les définitions drf-yasg pour une documentation API cohérente.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class IngestionSwaggerSchemas:
    """
    Schémas Swagger réutilisables pour l'API d'ingestion.
    """
    
    # Schéma de base pour une métrique
    METRICS_SCHEMA = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'timestamp': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                description="Horodatage de la collecte (format ISO 8601)"
            ),
            'cpu_usage': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0, 
                maximum=100,
                description="Utilisation CPU en pourcentage (0-100)"
            ),
            'memory_usage': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0, 
                maximum=100,
                description="Utilisation mémoire en pourcentage (0-100)"
            ),
            'latency_ms': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0,
                description="Latence en millisecondes"
            ),
            'disk_usage': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0, 
                maximum=100,
                description="Utilisation disque en pourcentage (0-100)"
            ),
            'network_in_kbps': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0,
                description="Trafic réseau entrant en Kbps"
            ),
            'network_out_kbps': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0,
                description="Trafic réseau sortant en Kbps"
            ),
            'io_wait': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0, 
                maximum=100,
                description="Temps d'attente I/O en pourcentage"
            ),
            'thread_count': openapi.Schema(
                type=openapi.TYPE_INTEGER, 
                minimum=0,
                description="Nombre de threads actifs"
            ),
            'active_connections': openapi.Schema(
                type=openapi.TYPE_INTEGER, 
                minimum=0,
                description="Nombre de connexions actives"
            ),
            'error_rate': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0, 
                maximum=1,
                description="Taux d'erreur (0.0 à 1.0)"
            ),
            'uptime_seconds': openapi.Schema(
                type=openapi.TYPE_INTEGER, 
                minimum=0,
                description="Temps de fonctionnement en secondes"
            ),
            'temperature_celsius': openapi.Schema(
                type=openapi.TYPE_NUMBER,
                description="Température en degrés Celsius"
            ),
            'power_consumption_watts': openapi.Schema(
                type=openapi.TYPE_NUMBER, 
                minimum=0,
                description="Consommation électrique en Watts"
            ),
            'service_status': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Statut des services (clé-valeur)"
            )
        },
        required=['timestamp', 'cpu_usage', 'memory_usage', 'latency_ms', 'disk_usage']
    )
    
    # Paramètres communs
    AUTO_ANALYZE_PARAM = openapi.Parameter(
        'auto_analyze',
        openapi.IN_QUERY,
        description="Lancer l'analyse automatique après ingestion",
        type=openapi.TYPE_BOOLEAN,
        default=False
    )
    
    BATCH_SIZE_PARAM = openapi.Parameter(
        'batch_size',
        openapi.IN_QUERY,
        description="Taille de lot pour le traitement (défaut: 100)",
        type=openapi.TYPE_INTEGER,
        default=100
    )
    
    CONTINUE_ON_ERROR_PARAM = openapi.Parameter(
        'continue_on_error',
        openapi.IN_QUERY,
        description="Continuer le traitement même en cas d'erreurs (défaut: true)",
        type=openapi.TYPE_BOOLEAN,
        default=True
    )
    
    # Réponses communes
    SUCCESS_RESPONSE = {
        201: openapi.Response(
            description='Ingestion réussie',
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
            description='Erreur de validation ou données invalides',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                    'error': openapi.Schema(type=openapi.TYPE_STRING),
                    'error_code': openapi.Schema(type=openapi.TYPE_STRING),
                    'details': openapi.Schema(type=openapi.TYPE_OBJECT)
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
    def get_data_ingestion_schema(cls):
        """Schéma pour l'endpoint d'ingestion de données."""
        return swagger_auto_schema(
            operation_description=(
                "Ingère des données de métriques d'infrastructure. "
                "Accepte une métrique unique ou un tableau de métriques."
            ),
            operation_summary="Ingestion de données",
            request_body=cls.METRICS_SCHEMA,
            manual_parameters=[
                cls.AUTO_ANALYZE_PARAM
            ],
            responses={
                201: openapi.Response(
                    description='Données ingérées avec succès',
                    schema=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                            'message': openapi.Schema(type=openapi.TYPE_STRING),
                            'code': openapi.Schema(type=openapi.TYPE_STRING),
                            'metrics_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'timestamp': openapi.Schema(type=openapi.TYPE_STRING),
                            'processing_duration_seconds': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'auto_analysis': openapi.Schema(type=openapi.TYPE_OBJECT)
                        }
                    )
                ),
                **cls.ERROR_RESPONSE
            },
            tags=['Ingestion']
        )
    
    @classmethod
    def get_bulk_ingestion_schema(cls):
        """Schéma pour l'endpoint d'ingestion en lot."""
        return swagger_auto_schema(
            operation_description="Ingère plusieurs métriques en lot de manière optimisée",
            operation_summary="Ingestion en lot",
            request_body=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=cls.METRICS_SCHEMA,
                description="Tableau de métriques à ingérer"
            ),
            manual_parameters=[
                cls.AUTO_ANALYZE_PARAM,
                cls.BATCH_SIZE_PARAM,
                cls.CONTINUE_ON_ERROR_PARAM
            ],
            responses={
                201: openapi.Response(
                    description='Ingestion en lot réussie',
                    schema=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
                            'message': openapi.Schema(type=openapi.TYPE_STRING),
                            'code': openapi.Schema(type=openapi.TYPE_STRING),
                            'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'ingested': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'errors': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'processing_duration_seconds': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'average_processing_time_ms': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'metrics_ids': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_INTEGER)
                            ),
                            'validation_errors': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING)
                            ),
                            'auto_analysis': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'total_analyzed': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'anomalies_detected': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'recommendations_generated': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'critical_issues': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        }
                    )
                ),
                **cls.ERROR_RESPONSE
            },
            tags=['Ingestion']
        )