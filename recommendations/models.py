from django.db import models
from django.utils import timezone
from ingestion.models import InfrastructureMetrics


class RecommendationReport(models.Model):
    """
    Modèle pour stocker les rapports de recommandations générés par l'IA.
    """
    
    # Relation avec les métriques analysées
    metrics = models.OneToOneField(
        InfrastructureMetrics,
        on_delete=models.CASCADE,
        related_name='recommendation_report',
        help_text="Métriques associées à ce rapport"
    )
    
    # Métadonnées du rapport
    generated_at = models.DateTimeField(
        default=timezone.now,
        help_text="Horodatage de génération du rapport"
    )
    
    # Contenu du rapport
    executive_summary = models.TextField(
        help_text="Résumé exécutif des recommandations"
    )
    
    detailed_analysis = models.TextField(
        help_text="Analyse détaillée de la situation"
    )
    
    recommendations_json = models.JSONField(
        help_text="Recommandations structurées en JSON"
    )
    
    # Priorités et actions
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Faible'),
            ('medium', 'Moyenne'),
            ('high', 'Élevée'),
            ('critical', 'Critique')
        ],
        default='medium',
        help_text="Niveau de priorité du rapport"
    )
    
    estimated_impact = models.CharField(
        max_length=50,
        help_text="Impact estimé des recommandations"
    )
    
    implementation_timeframe = models.CharField(
        max_length=100,
        help_text="Délai d'implémentation estimé"
    )
    
    # Méthode de génération
    generation_method = models.CharField(
        max_length=20,
        choices=[
            ('classic', 'Classique'),
            ('llm', 'LLM/IA')
        ],
        default='classic',
        help_text="Méthode utilisée pour générer ce rapport"
    )
    
    # Statut du rapport
    is_reviewed = models.BooleanField(
        default=False,
        help_text="Indique si le rapport a été examiné"
    )
    
    feedback = models.TextField(
        blank=True,
        help_text="Retour d'expérience sur les recommandations"
    )
    
    class Meta:
        verbose_name = "Rapport de Recommandation"
        verbose_name_plural = "Rapports de Recommandations"
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['generated_at']),
            models.Index(fields=['priority_level']),
            models.Index(fields=['is_reviewed']),
        ]
    
    def __str__(self):
        return f"Rapport {self.metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.priority_level}"
    
    @property
    def total_recommendations(self):
        """Compte le nombre total de recommandations."""
        if isinstance(self.recommendations_json, dict):
            return len(self.recommendations_json.get('actions', []))
        return 0
    
    @property
    def is_urgent(self):
        """Détermine si le rapport nécessite une action urgente."""
        return self.priority_level in ['high', 'critical']
    
    @property
    def recommendations(self):
        """Retourne la liste des recommandations."""
        if isinstance(self.recommendations_json, dict):
            return self.recommendations_json.get('actions', [])
        return []
