from django.db import models
from django.utils import timezone
import json


class InfrastructureMetrics(models.Model):
    """
    Modèle pour stocker les métriques d'infrastructure technique.
    Correspond au format JSON fourni dans les exigences du test.
    """
    
    # Identifiant et timestamp
    timestamp = models.DateTimeField(
        help_text="Horodatage de la collecte des métriques"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Date de création en base de données"
    )
    
    # Métriques de performance système
    cpu_usage = models.FloatField(
        help_text="Utilisation CPU en pourcentage (0-100)"
    )
    memory_usage = models.FloatField(
        help_text="Utilisation mémoire en pourcentage (0-100)"
    )
    latency_ms = models.FloatField(
        help_text="Latence en millisecondes"
    )
    disk_usage = models.FloatField(
        help_text="Utilisation disque en pourcentage (0-100)"
    )
    
    # Métriques réseau
    network_in_kbps = models.FloatField(
        help_text="Trafic réseau entrant en Kbps"
    )
    network_out_kbps = models.FloatField(
        help_text="Trafic réseau sortant en Kbps"
    )
    
    # Métriques avancées
    io_wait = models.FloatField(
        help_text="Temps d'attente I/O en pourcentage"
    )
    thread_count = models.IntegerField(
        help_text="Nombre de threads actifs"
    )
    active_connections = models.IntegerField(
        help_text="Nombre de connexions actives"
    )
    error_rate = models.FloatField(
        help_text="Taux d'erreur (0.0 à 1.0)"
    )
    
    # Métriques matérielles
    uptime_seconds = models.BigIntegerField(
        help_text="Temps de fonctionnement en secondes"
    )
    temperature_celsius = models.FloatField(
        help_text="Température en degrés Celsius"
    )
    power_consumption_watts = models.FloatField(
        help_text="Consommation électrique en Watts"
    )
    
    # Statuts des services (stocké en JSON)
    service_status = models.JSONField(
        help_text="Statut des services (database, api_gateway, cache, etc.)"
    )
    
    # Métadonnées
    is_anomalous = models.BooleanField(
        default=False,
        help_text="Indique si des anomalies ont été détectées"
    )
    analysis_completed = models.BooleanField(
        default=False,
        help_text="Indique si l'analyse a été effectuée"
    )
    
    class Meta:
        verbose_name = "Métrique d'Infrastructure"
        verbose_name_plural = "Métriques d'Infrastructure"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['is_anomalous']),
            models.Index(fields=['analysis_completed']),
        ]
    
    def __str__(self):
        return f"Métriques {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def uptime_hours(self):
        """Convertit le uptime en heures pour un affichage plus lisible."""
        return round(self.uptime_seconds / 3600, 2)
    
    @property
    def has_degraded_services(self):
        """Vérifie si des services sont en état dégradé."""
        if not self.service_status:
            return False
        return any(
            status in ['degraded', 'offline', 'error'] 
            for status in self.service_status.values()
        )


class AnomalyDetection(models.Model):
    """
    Modèle pour stocker les résultats de détection d'anomalies.
    """
    
    metrics = models.OneToOneField(
        InfrastructureMetrics,
        on_delete=models.CASCADE,
        related_name='anomaly_detection',
        help_text="Métriques associées à cette détection"
    )
    
    detected_at = models.DateTimeField(
        default=timezone.now,
        help_text="Horodatage de la détection d'anomalie"
    )
    
    # Types d'anomalies détectées
    cpu_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie CPU détectée"
    )
    memory_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie mémoire détectée"
    )
    latency_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie latence détectée"
    )
    disk_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie disque détectée"
    )
    io_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie I/O détectée"
    )
    error_rate_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie taux d'erreur détectée"
    )
    temperature_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie température détectée"
    )
    power_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie consommation détectée"
    )
    service_anomaly = models.BooleanField(
        default=False,
        help_text="Anomalie services détectée"
    )
    
    # Résumé des anomalies
    anomaly_summary = models.TextField(
        blank=True,
        help_text="Résumé textuel des anomalies détectées"
    )
    
    # Score de sévérité (0 = pas d'anomalie, 10 = critique)
    severity_score = models.IntegerField(
        default=0,
        help_text="Score de sévérité de 0 (normal) à 10 (critique)"
    )
    
    # Méthode d'analyse utilisée
    analysis_method = models.CharField(
        max_length=20,
        choices=[
            ('classic', 'Méthode Classique'),
            ('llm', 'Méthode LLM')
        ],
        default='classic',
        help_text="Méthode d'analyse utilisée pour détecter les anomalies"
    )
    
    class Meta:
        verbose_name = "Détection d'Anomalie"
        verbose_name_plural = "Détections d'Anomalies"
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"Anomalies {self.metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Score: {self.severity_score}"
    
    @property
    def total_anomalies(self):
        """Compte le nombre total d'anomalies détectées."""
        anomaly_fields = [
            'cpu_anomaly', 'memory_anomaly', 'latency_anomaly', 
            'disk_anomaly', 'io_anomaly', 'error_rate_anomaly',
            'temperature_anomaly', 'power_anomaly', 'service_anomaly'
        ]
        return sum(getattr(self, field) for field in anomaly_fields)
    
    @property
    def is_critical(self):
        """Détermine si l'anomalie est critique (score >= 7)."""
        return self.severity_score >= 7
