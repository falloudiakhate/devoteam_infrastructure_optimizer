"""
Détecteur d'anomalies classique basé sur des seuils configurables.
Méthode rapide et déterministe pour la détection d'anomalies.
"""

import logging
from typing import Dict, Optional
from django.conf import settings
from ingestion.models import InfrastructureMetrics, AnomalyDetection

logger = logging.getLogger(__name__)


class ClassicAnomalyDetector:
    """
    Détecteur d'anomalies basé sur des seuils configurables.
    Approche classique rapide et fiable.
    """
    
    def __init__(self):
        self.thresholds = getattr(settings, 'ANOMALY_THRESHOLDS', {
            'cpu_usage': 80,
            'memory_usage': 85,
            'latency_ms': 500,
            'disk_usage': 90,
            'io_wait': 20,
            'error_rate': 0.05,
            'temperature_celsius': 75,
            'power_consumption_watts': 400
        })
    
    def detect_anomalies(self, metrics: InfrastructureMetrics) -> Dict[str, bool]:
        """
        Détecte les anomalies basées sur des seuils prédéfinis.
        
        Args:
            metrics: Instance des métriques à analyser
            
        Returns:
            Dict: Dictionnaire des anomalies détectées par type
        """
        anomalies = {}
        
        # Vérification CPU
        cpu_threshold = self.thresholds.get('cpu_usage', 80)
        anomalies['cpu_anomaly'] = metrics.cpu_usage > cpu_threshold
        
        # Vérification mémoire
        memory_threshold = self.thresholds.get('memory_usage', 85)
        anomalies['memory_anomaly'] = metrics.memory_usage > memory_threshold
        
        # Vérification latence
        latency_threshold = self.thresholds.get('latency_ms', 500)
        anomalies['latency_anomaly'] = metrics.latency_ms > latency_threshold
        
        # Vérification disque
        disk_threshold = self.thresholds.get('disk_usage', 90)
        anomalies['disk_anomaly'] = metrics.disk_usage > disk_threshold
        
        # Vérification I/O wait
        io_threshold = self.thresholds.get('io_wait', 20)
        anomalies['io_anomaly'] = metrics.io_wait > io_threshold
        
        # Vérification taux d'erreur
        error_threshold = self.thresholds.get('error_rate', 0.05)
        anomalies['error_rate_anomaly'] = metrics.error_rate > error_threshold
        
        # Vérification température
        temp_threshold = self.thresholds.get('temperature_celsius', 75)
        anomalies['temperature_anomaly'] = metrics.temperature_celsius > temp_threshold
        
        # Vérification consommation électrique
        power_threshold = self.thresholds.get('power_consumption_watts', 400)
        anomalies['power_anomaly'] = metrics.power_consumption_watts > power_threshold
        
        # Vérification services dégradés
        anomalies['service_anomaly'] = metrics.has_degraded_services
        
        if any(anomalies.values()):
            logger.info(f"Anomalies classiques détectées pour les métriques {metrics.id}")
        
        return anomalies
    
    def calculate_severity_score(self, anomalies: Dict[str, bool]) -> int:
        """
        Calcule un score de sévérité basé sur les anomalies détectées.
        
        Args:
            anomalies: Dictionnaire des anomalies détectées
            
        Returns:
            int: Score de sévérité de 0 (normal) à 10 (critique)
        """
        # Pondération des différents types d'anomalies
        weights = {
            'cpu_anomaly': 2,
            'memory_anomaly': 2,
            'disk_anomaly': 3,
            'latency_anomaly': 2,
            'io_anomaly': 1,
            'error_rate_anomaly': 3,
            'temperature_anomaly': 2,
            'power_anomaly': 1,
            'service_anomaly': 3
        }
        
        score = 0
        for anomaly_type, detected in anomalies.items():
            if detected and anomaly_type in weights:
                score += weights[anomaly_type]
        
        return min(score, 10)
    
    def generate_summary(self, anomalies: Dict[str, bool], 
                        metrics: InfrastructureMetrics) -> str:
        """
        Génère un résumé textuel des anomalies détectées.
        
        Args:
            anomalies: Dictionnaire des anomalies détectées
            metrics: Métriques analysées
            
        Returns:
            str: Résumé des anomalies en français
        """
        anomaly_messages = []
        
        if anomalies.get('cpu_anomaly'):
            anomaly_messages.append(f"CPU élevé: {metrics.cpu_usage}%")
        
        if anomalies.get('memory_anomaly'):
            anomaly_messages.append(f"Mémoire élevée: {metrics.memory_usage}%")
        
        if anomalies.get('latency_anomaly'):
            anomaly_messages.append(f"Latence: {metrics.latency_ms}ms")
        
        if anomalies.get('disk_anomaly'):
            anomaly_messages.append(f"Disque critique: {metrics.disk_usage}%")
        
        if anomalies.get('io_anomaly'):
            anomaly_messages.append(f"I/O wait élevé: {metrics.io_wait}%")
        
        if anomalies.get('error_rate_anomaly'):
            anomaly_messages.append(f"Erreurs: {metrics.error_rate*100:.2f}%")
        
        if anomalies.get('temperature_anomaly'):
            anomaly_messages.append(f"Température: {metrics.temperature_celsius}°C")
        
        if anomalies.get('power_anomaly'):
            anomaly_messages.append(f"Consommation: {metrics.power_consumption_watts}W")
        
        if anomalies.get('service_anomaly'):
            degraded_services = [
                service for service, status in metrics.service_status.items()
                if status in ['degraded', 'offline', 'error']
            ]
            if degraded_services:
                anomaly_messages.append(f"Services dégradés: {', '.join(degraded_services[:3])}")
        
        if not anomaly_messages:
            return "Aucune anomalie détectée par analyse classique"
        
        return "Analyse classique - Seuils dépassés: " + "; ".join(anomaly_messages)
    
    def analyze_metrics(self, metrics: InfrastructureMetrics) -> Optional[AnomalyDetection]:
        """
        Analyse complète des métriques avec la méthode classique.
        
        Args:
            metrics: Instance des métriques à analyser
            
        Returns:
            AnomalyDetection: Instance créée ou None si erreur
        """
        try:
            logger.info(f"Analyse classique des métriques {metrics.id}")
            
            # Détection des anomalies
            anomalies = self.detect_anomalies(metrics)
            
            # Calcul du score de sévérité
            severity_score = self.calculate_severity_score(anomalies)
            
            # Génération du résumé
            summary = self.generate_summary(anomalies, metrics)
            
            # Création de l'instance AnomalyDetection
            anomaly_detection = AnomalyDetection.objects.create(
                metrics=metrics,
                **anomalies,
                anomaly_summary=summary,
                severity_score=severity_score,
                analysis_method='classic'
            )
            
            # Mise à jour du statut des métriques
            metrics.is_anomalous = any(anomalies.values())
            metrics.analysis_completed = True
            metrics.save()
            
            logger.info(f"Analyse classique terminée pour {metrics.id} - Score: {severity_score}")
            return anomaly_detection
            
        except Exception as e:
            logger.error(f"Erreur analyse classique métrique {metrics.id}: {e}")
            return None
    
    def analyze_batch_metrics(self, metrics_queryset) -> Dict[str, int]:
        """
        Analyse un lot de métriques avec la méthode classique.
        
        Args:
            metrics_queryset: QuerySet des métriques à analyser
            
        Returns:
            Dict: Statistiques d'analyse
        """
        results = {
            'total': metrics_queryset.count(),
            'analyzed': 0,
            'errors': 0,
            'anomalies_detected': 0
        }
        
        for metrics in metrics_queryset:
            try:
                anomaly_detection = self.analyze_metrics(metrics)
                if anomaly_detection:
                    results['analyzed'] += 1
                    if anomaly_detection.total_anomalies > 0:
                        results['anomalies_detected'] += 1
                else:
                    results['errors'] += 1
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Erreur analyse lot classique métrique {metrics.id}: {e}")
        
        logger.info(f"Analyse classique lot terminée: {results['analyzed']}/{results['total']} succès")
        return results