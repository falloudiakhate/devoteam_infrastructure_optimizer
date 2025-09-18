import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from .models import InfrastructureMetrics

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Service responsable de l'ingestion des données de métriques d'infrastructure.
    
    Ce service traite les données JSON reçues et les sauvegarde en base de données
    en respectant le format défini dans les exigences du test Devoteam.
    """
    
    @staticmethod
    def validate_metrics_data(data: Dict) -> bool:
        """
        Valide les données de métriques avant ingestion.
        
        Args:
            data: Dictionnaire contenant les données de métriques
            
        Returns:
            bool: True si les données sont valides, False sinon
        """
        required_fields = [
            'timestamp', 'cpu_usage', 'memory_usage', 'latency_ms',
            'disk_usage', 'network_in_kbps', 'network_out_kbps',
            'io_wait', 'thread_count', 'active_connections', 
            'error_rate', 'uptime_seconds', 'temperature_celsius',
            'power_consumption_watts', 'service_status'
        ]
        
        # Vérifier que tous les champs obligatoires sont présents
        for field in required_fields:
            if field not in data:
                logger.error(f"Champ manquant dans les données: {field}")
                return False
        
        # Validation des types et des plages de valeurs
        try:
            # Validation des pourcentages (0-100)
            percentage_fields = ['cpu_usage', 'memory_usage', 'disk_usage', 'io_wait']
            for field in percentage_fields:
                value = float(data[field])
                if not (0 <= value <= 100):
                    logger.error(f"Valeur invalide pour {field}: {value} (doit être entre 0 et 100)")
                    return False
            
            # Validation du taux d'erreur (0-1)
            error_rate = float(data['error_rate'])
            if not (0 <= error_rate <= 1):
                logger.error(f"Taux d'erreur invalide: {error_rate} (doit être entre 0 et 1)")
                return False
            
            # Validation des valeurs positives
            positive_fields = [
                'latency_ms', 'network_in_kbps', 'network_out_kbps',
                'thread_count', 'active_connections', 'uptime_seconds',
                'temperature_celsius', 'power_consumption_watts'
            ]
            for field in positive_fields:
                value = float(data[field]) if field != 'thread_count' and field != 'active_connections' else int(data[field])
                if value < 0:
                    logger.error(f"Valeur négative pour {field}: {value}")
                    return False
            
            # Validation du service_status
            if not isinstance(data['service_status'], dict):
                logger.error("service_status doit être un dictionnaire")
                return False
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur de validation des données: {e}")
            return False
    
    @staticmethod
    def parse_timestamp(timestamp_input) -> datetime:
        """
        Parse le timestamp au format ISO 8601.
        
        Args:
            timestamp_input: Chaîne de caractères ou objet datetime du timestamp
            
        Returns:
            datetime: Objet datetime parsé
        """
        try:
            # Si c'est déjà un objet datetime, le retourner tel quel
            if isinstance(timestamp_input, datetime):
                return timestamp_input
            
            # Sinon, traiter comme une chaîne
            timestamp_str = str(timestamp_input)
            
            # Gestion du format ISO 8601 avec Z
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError) as e:
            logger.error(f"Erreur de parsing du timestamp {timestamp_input}: {e}")
            # Fallback sur l'heure actuelle
            return timezone.now()
    
    @staticmethod
    def ingest_metrics_data(data: Dict) -> Optional[InfrastructureMetrics]:
        """
        Ingère les données de métriques dans la base de données.
        
        Args:
            data: Dictionnaire contenant les données de métriques
            
        Returns:
            InfrastructureMetrics: Instance créée ou None si erreur
        """
        try:
            # Validation préalable des données
            if not DataIngestionService.validate_metrics_data(data):
                logger.error("Données de métriques invalides")
                return None
            
            # Parse du timestamp
            timestamp = DataIngestionService.parse_timestamp(data['timestamp'])
            
            # Création de l'instance avec transaction pour assurer la cohérence
            with transaction.atomic():
                metrics = InfrastructureMetrics.objects.create(
                    timestamp=timestamp,
                    cpu_usage=float(data['cpu_usage']),
                    memory_usage=float(data['memory_usage']),
                    latency_ms=float(data['latency_ms']),
                    disk_usage=float(data['disk_usage']),
                    network_in_kbps=float(data['network_in_kbps']),
                    network_out_kbps=float(data['network_out_kbps']),
                    io_wait=float(data['io_wait']),
                    thread_count=int(data['thread_count']),
                    active_connections=int(data['active_connections']),
                    error_rate=float(data['error_rate']),
                    uptime_seconds=int(data['uptime_seconds']),
                    temperature_celsius=float(data['temperature_celsius']),
                    power_consumption_watts=float(data['power_consumption_watts']),
                    service_status=data['service_status']
                )
                
                logger.info(f"Données de métriques ingérées avec succès: {metrics.id}")
                return metrics
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ingestion des données: {e}")
            return None
    
    @staticmethod
    def ingest_batch_metrics(metrics_list: List[Dict]) -> Dict:
        """
        Ingère un lot de données de métriques.
        
        Args:
            metrics_list: Liste de dictionnaires contenant les données
            
        Returns:
            Dict: Statistiques d'ingestion avec IDs et instances
        """
        results = {
            'total': len(metrics_list),
            'success': 0,
            'errors': 0,
            'error_details': [],
            'metrics_ids': [],
            'metrics_instances': []
        }
        
        for i, data in enumerate(metrics_list):
            try:
                metrics = DataIngestionService.ingest_metrics_data(data)
                if metrics:
                    results['success'] += 1
                    results['metrics_ids'].append(metrics.id)
                    results['metrics_instances'].append(metrics)
                else:
                    results['errors'] += 1
                    results['error_details'].append(f"Erreur ligne {i+1}: Validation échouée")
                    
            except Exception as e:
                results['errors'] += 1
                results['error_details'].append(f"Erreur ligne {i+1}: {str(e)}")
                logger.error(f"Erreur ingestion lot ligne {i+1}: {e}")
        
        # Maintenir la compatibilité avec l'ancienne interface
        results['error'] = results['errors']
        results['errors_list'] = results['error_details']
        
        logger.info(f"Ingestion lot terminée: {results['success']}/{results['total']} succès")
        return results
    
    @staticmethod
    def load_from_json_file(file_path: str) -> Dict[str, int]:
        """
        Charge et ingère les données depuis un fichier JSON.
        
        Args:
            file_path: Chemin vers le fichier JSON
            
        Returns:
            Dict: Statistiques d'ingestion
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Si c'est un seul objet, le convertir en liste
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise ValueError("Le fichier JSON doit contenir un objet ou une liste d'objets")
            
            return DataIngestionService.ingest_batch_metrics(data)
            
        except FileNotFoundError:
            logger.error(f"Fichier non trouvé: {file_path}")
            return {'total': 0, 'success': 0, 'error': 1, 'errors': [f"Fichier non trouvé: {file_path}"]}
        
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {e}")
            return {'total': 0, 'success': 0, 'error': 1, 'errors': [f"Erreur JSON: {str(e)}"]}
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier: {e}")
            return {'total': 0, 'success': 0, 'error': 1, 'errors': [f"Erreur: {str(e)}"]}


class RealTimeDataProcessor:
    """
    Processeur pour les données en temps réel.
    
    Cette classe peut être étendue pour traiter des flux de données
    en temps réel depuis des sources comme Kafka, RabbitMQ, etc.
    """
    
    def __init__(self):
        self.ingestion_service = DataIngestionService()
    
    def process_stream_data(self, data: Dict) -> bool:
        """
        Traite une donnée reçue en streaming.
        
        Args:
            data: Données de métriques reçues
            
        Returns:
            bool: True si traitement réussi, False sinon
        """
        metrics = self.ingestion_service.ingest_metrics_data(data)
        return metrics is not None
    
    def start_stream_processing(self):
        """
        Point d'entrée pour démarrer le traitement en temps réel.
        À implémenter selon le système de streaming choisi.
        """
        logger.info("Démarrage du traitement en temps réel")
        # TODO: Implémenter selon le choix de technologie (Kafka, WebSocket, etc.)