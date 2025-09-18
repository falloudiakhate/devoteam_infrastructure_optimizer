"""
Générateur de recommandations classique basé sur des règles.
Analyse les métriques et génère des recommandations selon des patterns prédéfinis.
"""

import logging
from typing import Dict, List, Optional
from django.utils import timezone
from ingestion.models import InfrastructureMetrics
from recommendations.models import RecommendationReport

logger = logging.getLogger(__name__)


class ClassicRecommendationGenerator:
    """
    Générateur de recommandations basé sur des règles métier prédéfinies.
    Approche déterministe et rapide.
    """
    
    def __init__(self):
        self.rules = self._initialize_recommendation_rules()
    
    def _initialize_recommendation_rules(self) -> Dict:
        """
        Initialise les règles de recommandations basées sur les seuils.
        
        Returns:
            Dict: Règles structurées par catégorie
        """
        return {
            'cpu': {
                'high_threshold': 80,
                'critical_threshold': 95,
                'recommendations': {
                    'high': {
                        'title': 'Optimisation CPU',
                        'description': 'Usage CPU élevé détecté. Considérer l\'ajout de ressources ou l\'optimisation des processus.',
                        'priority': 'high',
                        'category': 'performance'
                    },
                    'critical': {
                        'title': 'CPU critique - Action immédiate',
                        'description': 'Usage CPU critique. Intervention immédiate requise pour éviter la dégradation.',
                        'priority': 'critical',
                        'category': 'performance'
                    }
                }
            },
            'memory': {
                'high_threshold': 85,
                'critical_threshold': 95,
                'recommendations': {
                    'high': {
                        'title': 'Gestion mémoire',
                        'description': 'Usage mémoire élevé. Augmenter la RAM disponible ou optimiser l\'utilisation.',
                        'priority': 'high',
                        'category': 'resources'
                    },
                    'critical': {
                        'title': 'Mémoire critique',
                        'description': 'Risque d\'épuisement mémoire. Extension immédiate de la RAM recommandée.',
                        'priority': 'critical',
                        'category': 'resources'
                    }
                }
            },
            'disk': {
                'high_threshold': 85,
                'critical_threshold': 95,
                'recommendations': {
                    'high': {
                        'title': 'Gestion espace disque',
                        'description': 'Espace disque réduit. Nettoyer les fichiers temporaires et planifier l\'extension.',
                        'priority': 'high',
                        'category': 'storage'
                    },
                    'critical': {
                        'title': 'Espace disque critique',
                        'description': 'Risque de saturation disque. Extension ou nettoyage immédiat requis.',
                        'priority': 'critical',
                        'category': 'storage'
                    }
                }
            },
            'latency': {
                'high_threshold': 300,
                'critical_threshold': 1000,
                'recommendations': {
                    'high': {
                        'title': 'Optimisation latence',
                        'description': 'Latence élevée détectée. Optimiser les requêtes et connexions réseau.',
                        'priority': 'medium',
                        'category': 'network'
                    },
                    'critical': {
                        'title': 'Latence critique',
                        'description': 'Latence excessive impactant les utilisateurs. Investigation réseau urgente.',
                        'priority': 'critical',
                        'category': 'network'
                    }
                }
            },
            'temperature': {
                'high_threshold': 70,
                'critical_threshold': 80,
                'recommendations': {
                    'high': {
                        'title': 'Gestion thermique',
                        'description': 'Température élevée. Vérifier la ventilation et l\'environnement.',
                        'priority': 'medium',
                        'category': 'hardware'
                    },
                    'critical': {
                        'title': 'Surchauffe critique',
                        'description': 'Risque de surchauffe. Arrêt préventif et inspection du refroidissement requis.',
                        'priority': 'critical',
                        'category': 'hardware'
                    }
                }
            }
        }
    
    def generate_recommendations(self, metrics: InfrastructureMetrics,
                               anomalies_summary: str = "") -> Dict:
        """
        Génère des recommandations basées sur l'analyse des métriques.
        
        Args:
            metrics: Métriques d'infrastructure à analyser
            anomalies_summary: Résumé des anomalies détectées
            
        Returns:
            Dict: Recommandations structurées
        """
        logger.info(f"Génération recommandations classiques pour métrique {metrics.id}")
        
        recommendations = []
        priority_level = "low"
        
        # Analyse CPU
        cpu_rec = self._analyze_cpu(metrics.cpu_usage)
        if cpu_rec:
            recommendations.append(cpu_rec)
            priority_level = self._update_priority(priority_level, cpu_rec['priority'])
        
        # Analyse mémoire
        memory_rec = self._analyze_memory(metrics.memory_usage)
        if memory_rec:
            recommendations.append(memory_rec)
            priority_level = self._update_priority(priority_level, memory_rec['priority'])
        
        # Analyse disque
        disk_rec = self._analyze_disk(metrics.disk_usage)
        if disk_rec:
            recommendations.append(disk_rec)
            priority_level = self._update_priority(priority_level, disk_rec['priority'])
        
        # Analyse latence
        latency_rec = self._analyze_latency(metrics.latency_ms)
        if latency_rec:
            recommendations.append(latency_rec)
            priority_level = self._update_priority(priority_level, latency_rec['priority'])
        
        # Analyse température
        temp_rec = self._analyze_temperature(metrics.temperature_celsius)
        if temp_rec:
            recommendations.append(temp_rec)
            priority_level = self._update_priority(priority_level, temp_rec['priority'])
        
        # Analyse services
        service_rec = self._analyze_services(metrics)
        if service_rec:
            recommendations.append(service_rec)
            priority_level = self._update_priority(priority_level, service_rec['priority'])
        
        # Analyse des erreurs
        error_rec = self._analyze_errors(metrics.error_rate)
        if error_rec:
            recommendations.append(error_rec)
            priority_level = self._update_priority(priority_level, error_rec['priority'])
        
        # Recommandation de monitoring si tout va bien
        if not recommendations:
            recommendations.append({
                'title': 'Surveillance continue',
                'description': 'Infrastructure stable. Maintenir la surveillance proactive des métriques.',
                'priority': 'low',
                'category': 'monitoring'
            })
        
        # Construction de la réponse
        return self._build_response(recommendations, priority_level, anomalies_summary)
    
    def _analyze_cpu(self, cpu_usage: float) -> Optional[Dict]:
        """Analyse l'usage CPU et retourne une recommandation si nécessaire."""
        rules = self.rules['cpu']
        
        if cpu_usage >= rules['critical_threshold']:
            rec = rules['recommendations']['critical'].copy()
            rec['description'] = f"CPU à {cpu_usage}%. {rec['description']}"
            return rec
        elif cpu_usage >= rules['high_threshold']:
            rec = rules['recommendations']['high'].copy()
            rec['description'] = f"CPU à {cpu_usage}%. {rec['description']}"
            return rec
        
        return None
    
    def _analyze_memory(self, memory_usage: float) -> Optional[Dict]:
        """Analyse l'usage mémoire et retourne une recommandation si nécessaire."""
        rules = self.rules['memory']
        
        if memory_usage >= rules['critical_threshold']:
            rec = rules['recommendations']['critical'].copy()
            rec['description'] = f"Mémoire à {memory_usage}%. {rec['description']}"
            return rec
        elif memory_usage >= rules['high_threshold']:
            rec = rules['recommendations']['high'].copy()
            rec['description'] = f"Mémoire à {memory_usage}%. {rec['description']}"
            return rec
        
        return None
    
    def _analyze_disk(self, disk_usage: float) -> Optional[Dict]:
        """Analyse l'usage disque et retourne une recommandation si nécessaire."""
        rules = self.rules['disk']
        
        if disk_usage >= rules['critical_threshold']:
            rec = rules['recommendations']['critical'].copy()
            rec['description'] = f"Disque à {disk_usage}%. {rec['description']}"
            return rec
        elif disk_usage >= rules['high_threshold']:
            rec = rules['recommendations']['high'].copy()
            rec['description'] = f"Disque à {disk_usage}%. {rec['description']}"
            return rec
        
        return None
    
    def _analyze_latency(self, latency_ms: float) -> Optional[Dict]:
        """Analyse la latence et retourne une recommandation si nécessaire."""
        rules = self.rules['latency']
        
        if latency_ms >= rules['critical_threshold']:
            rec = rules['recommendations']['critical'].copy()
            rec['description'] = f"Latence {latency_ms}ms. {rec['description']}"
            return rec
        elif latency_ms >= rules['high_threshold']:
            rec = rules['recommendations']['high'].copy()
            rec['description'] = f"Latence {latency_ms}ms. {rec['description']}"
            return rec
        
        return None
    
    def _analyze_temperature(self, temperature: float) -> Optional[Dict]:
        """Analyse la température et retourne une recommandation si nécessaire."""
        rules = self.rules['temperature']
        
        if temperature >= rules['critical_threshold']:
            rec = rules['recommendations']['critical'].copy()
            rec['description'] = f"Température {temperature}°C. {rec['description']}"
            return rec
        elif temperature >= rules['high_threshold']:
            rec = rules['recommendations']['high'].copy()
            rec['description'] = f"Température {temperature}°C. {rec['description']}"
            return rec
        
        return None
    
    def _analyze_services(self, metrics: InfrastructureMetrics) -> Optional[Dict]:
        """Analyse les services et retourne une recommandation si nécessaire."""
        if metrics.has_degraded_services:
            degraded_services = [
                service for service, status in metrics.service_status.items()
                if status in ['degraded', 'offline', 'error']
            ]
            
            return {
                'title': 'Services dégradés détectés',
                'description': f"Services en état dégradé: {', '.join(degraded_services[:3])}. Redémarrage ou investigation requise.",
                'priority': 'high',
                'category': 'services'
            }
        
        return None
    
    def _analyze_errors(self, error_rate: float) -> Optional[Dict]:
        """Analyse le taux d'erreur et retourne une recommandation si nécessaire."""
        error_percentage = error_rate * 100
        
        if error_percentage > 5:
            return {
                'title': 'Taux d\'erreur élevé',
                'description': f"Taux d'erreur de {error_percentage:.2f}%. Investigation des logs et correction des erreurs recommandée.",
                'priority': 'high',
                'category': 'reliability'
            }
        elif error_percentage > 1:
            return {
                'title': 'Surveillance des erreurs',
                'description': f"Taux d'erreur de {error_percentage:.2f}%. Monitoring renforcé recommandé.",
                'priority': 'medium',
                'category': 'reliability'
            }
        
        return None
    
    def _update_priority(self, current: str, new: str) -> str:
        """Met à jour le niveau de priorité global."""
        priority_order = ['low', 'medium', 'high', 'critical']
        
        current_idx = priority_order.index(current) if current in priority_order else 0
        new_idx = priority_order.index(new) if new in priority_order else 0
        
        return priority_order[max(current_idx, new_idx)]
    
    def _build_response(self, recommendations: List[Dict], 
                       priority_level: str, anomalies_summary: str) -> Dict:
        """Construit la réponse finale structurée."""
        # Génération du résumé exécutif
        rec_count = len(recommendations)
        critical_count = sum(1 for r in recommendations if r['priority'] == 'critical')
        
        if critical_count > 0:
            exec_summary = f"Analyse critique: {critical_count} problèmes critiques parmi {rec_count} recommandations. Action immédiate requise."
        elif priority_level == 'high':
            exec_summary = f"Attention: {rec_count} recommandations prioritaires identifiées pour optimiser l'infrastructure."
        else:
            exec_summary = f"Analyse de {rec_count} points d'amélioration identifiés pour maintenir la performance."
        
        # Analyse détaillée
        detailed_analysis = f"Analyse basée sur les règles métier prédéfinies. Anomalies détectées: {anomalies_summary or 'Aucune anomalie majeure'}. "
        detailed_analysis += f"Les métriques révèlent {rec_count} axes d'amélioration répartis sur plusieurs catégories système."
        
        # Délai d'implémentation basé sur la priorité
        timeframe_map = {
            'critical': 'Immédiat (< 4h)',
            'high': '1-3 jours',
            'medium': '1-2 semaines',
            'low': '1 mois'
        }
        
        return {
            'executive_summary': exec_summary,
            'detailed_analysis': detailed_analysis,
            'recommendations': recommendations,
            'priority_level': priority_level,
            'estimated_impact': 'Amélioration de la stabilité et des performances système',
            'implementation_timeframe': timeframe_map.get(priority_level, '1-2 semaines')
        }
    
    def generate_report(self, metrics: InfrastructureMetrics) -> Optional[RecommendationReport]:
        """
        Génère un rapport complet avec la méthode classique.
        
        Args:
            metrics: Métriques à analyser
            
        Returns:
            RecommendationReport: Rapport généré ou None
        """
        try:
            # Récupération du résumé des anomalies
            anomalies_summary = "Aucune anomalie détectée"
            if hasattr(metrics, 'anomaly_detection') and metrics.anomaly_detection:
                anomalies_summary = metrics.anomaly_detection.anomaly_summary
            
            # Génération des recommandations
            recommendations_data = self.generate_recommendations(metrics, anomalies_summary)
            
            # Création ou mise à jour du rapport
            report, created = RecommendationReport.objects.update_or_create(
                metrics=metrics,
                defaults={
                    'executive_summary': recommendations_data['executive_summary'],
                    'detailed_analysis': recommendations_data['detailed_analysis'],
                    'recommendations_json': {'actions': recommendations_data['recommendations']},
                    'priority_level': recommendations_data['priority_level'],
                    'estimated_impact': recommendations_data['estimated_impact'],
                    'implementation_timeframe': recommendations_data['implementation_timeframe'],
                    'generation_method': 'classic',
                    'generated_at': timezone.now()
                }
            )
            
            action = "créé" if created else "mis à jour"
            logger.info(f"Rapport classique {action}: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Erreur génération rapport classique: {e}")
            return None