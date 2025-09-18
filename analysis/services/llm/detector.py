"""
Détecteur d'anomalies intelligent basé sur les LLMs.
Interface principale pour l'analyse via Azure OpenAI.
"""

import logging
from typing import Dict, Any, Optional
from ingestion.models import InfrastructureMetrics, AnomalyDetection
from .engine import LLMAnalysisEngine
from .prompts import AnomalyAnalysisPrompts

logger = logging.getLogger(__name__)


class LLMAnomalyDetector:
    """
    Détecteur d'anomalies intelligent utilisant Azure OpenAI.
    Analyse contextuelle avancée avec explications détaillées.
    """
    
    def __init__(self):
        self.llm_engine = LLMAnalysisEngine()
        self.prompts = AnomalyAnalysisPrompts()
    
    def _prepare_metrics_data(self, metrics: InfrastructureMetrics) -> Dict[str, Any]:
        """
        Prépare les données de métriques pour l'analyse LLM.
        
        Args:
            metrics: Instance des métriques
            
        Returns:
            Dict: Données formatées pour l'analyse LLM
        """
        return {
            'timestamp': metrics.timestamp.isoformat() if metrics.timestamp else None,
            'cpu_usage': metrics.cpu_usage,
            'memory_usage': metrics.memory_usage,
            'latency_ms': metrics.latency_ms,
            'disk_usage': metrics.disk_usage,
            'network_in_kbps': metrics.network_in_kbps,
            'network_out_kbps': metrics.network_out_kbps,
            'io_wait': metrics.io_wait,
            'thread_count': metrics.thread_count,
            'active_connections': metrics.active_connections,
            'error_rate': metrics.error_rate,
            'uptime_hours': metrics.uptime_hours,
            'temperature_celsius': metrics.temperature_celsius,
            'power_consumption_watts': metrics.power_consumption_watts,
            'service_status': metrics.service_status,
            'has_degraded_services': metrics.has_degraded_services
        }
    
    def detect_anomalies(self, metrics: InfrastructureMetrics) -> Optional[Dict[str, Any]]:
        """
        Détecte les anomalies via analyse LLM intelligente.
        
        Args:
            metrics: Instance des métriques à analyser
            
        Returns:
            Dict: Analyse complète avec explications et recommandations, ou None si LLM indisponible
        """
        if not self.llm_engine.is_available:
            logger.info("LLM non configuré, analyse non disponible")
            return None
        
        try:
            # Préparation des données
            metrics_data = self._prepare_metrics_data(metrics)
            
            # Analyse principale des anomalies
            anomaly_analysis = self.llm_engine.detect_anomalies(metrics_data)
            
            if not anomaly_analysis:
                logger.warning("Échec analyse LLM")
                return None
            
            # Analyses complémentaires si l'analyse principale réussit
            severity_analysis = self.llm_engine.assess_severity(metrics_data)
            correlation_analysis = self.llm_engine.analyze_correlations(metrics_data)
            
            # Fusion des résultats
            complete_analysis = self._merge_llm_analyses(
                anomaly_analysis, severity_analysis, correlation_analysis
            )
            
            logger.info(f"Analyse LLM complète terminée pour métrique {metrics.id}")
            return complete_analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse LLM métrique {metrics.id}: {e}")
            return None
    
    def _merge_llm_analyses(self, anomaly_analysis: Dict[str, Any],
                           severity_analysis: Optional[Dict[str, Any]],
                           correlation_analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fusionne les différentes analyses LLM en un résultat complet.
        
        Args:
            anomaly_analysis: Analyse principale des anomalies
            severity_analysis: Analyse de sévérité (optionnelle)
            correlation_analysis: Analyse de corrélations (optionnelle)
            
        Returns:
            Dict: Analyse complète fusionnée
        """
        complete_analysis = anomaly_analysis.copy()
        
        # Enrichissement avec l'analyse de sévérité
        if severity_analysis:
            complete_analysis.update({
                'severity_justification': severity_analysis.get('severity_justification', ''),
                'immediate_risk': severity_analysis.get('immediate_risk', False),
                'cascade_risk': severity_analysis.get('cascade_risk', False),
                'business_impact': severity_analysis.get('business_impact', 'inconnu'),
                'time_to_failure': severity_analysis.get('time_to_failure', 'indéterminé')
            })
            
            # Mise à jour du score de sévérité si fourni
            if 'severity_score' in severity_analysis:
                complete_analysis['severity_score'] = severity_analysis['severity_score']
        
        # Enrichissement avec l'analyse de corrélations
        if correlation_analysis:
            existing_correlations = complete_analysis.get('correlations_found', [])
            new_correlations = []
            
            for corr in correlation_analysis.get('strong_correlations', []):
                correlation_desc = f"{' & '.join(corr.get('metrics_pair', []))}: {corr.get('explanation', 'corrélation détectée')}"
                new_correlations.append(correlation_desc)
            
            complete_analysis['correlations_found'] = existing_correlations + new_correlations[:3]
            complete_analysis['correlation_insights'] = correlation_analysis.get('insights', [])
        
        return complete_analysis
    
    
    def generate_llm_summary(self, llm_analysis: Dict[str, Any], 
                           metrics: InfrastructureMetrics) -> str:
        """
        Génère un résumé basé sur l'analyse LLM.
        
        Args:
            llm_analysis: Résultats de l'analyse LLM
            metrics: Métriques analysées
            
        Returns:
            str: Résumé formaté de l'analyse LLM
        """
        summary_parts = []
        
        # Évaluation du risque
        risk_assessment = llm_analysis.get('risk_assessment', '')
        if risk_assessment and 'indisponible' not in risk_assessment.lower():
            summary_parts.append(f"LLM: {risk_assessment}")
        
        # Explications des anomalies
        explanations = llm_analysis.get('anomaly_explanations', [])
        if explanations and explanations != ['Analyse LLM non disponible']:
            summary_parts.append(f"Détails: {'; '.join(explanations[:2])}")
        
        # Corrélations découvertes
        correlations = llm_analysis.get('correlations_found', [])
        if correlations:
            summary_parts.append(f"Corrélations: {'; '.join(correlations[:2])}")
        
        if not summary_parts:
            return "Analyse LLM: Aucune anomalie significative détectée"
        
        return " | ".join(summary_parts)
    
    def analyze_metrics(self, metrics: InfrastructureMetrics) -> Optional[AnomalyDetection]:
        """
        Analyse complète des métriques avec méthode LLM pure.
        
        Args:
            metrics: Instance des métriques à analyser
            
        Returns:
            AnomalyDetection: Instance créée ou None si LLM indisponible ou erreur
        """
        try:
            logger.info(f"Analyse LLM des métriques {metrics.id}")
            
            # Analyse LLM complète
            llm_analysis = self.detect_anomalies(metrics)
            
            if not llm_analysis:
                logger.info(f"Analyse LLM non disponible pour métrique {metrics.id}")
                return None
            
            # Conversion des anomalies LLM vers le format modèle
            model_anomalies = self._convert_llm_to_model_format(llm_analysis)
            
            # Score de sévérité
            severity_score = llm_analysis.get('severity_score', 5)
            
            # Génération du résumé
            summary = self.generate_llm_summary(llm_analysis, metrics)
            
            # Création de l'instance AnomalyDetection
            anomaly_detection = AnomalyDetection.objects.create(
                metrics=metrics,
                **model_anomalies,
                anomaly_summary=summary,
                severity_score=severity_score,
                analysis_method='llm'
            )
            
            # Mise à jour du statut des métriques
            metrics.is_anomalous = llm_analysis.get('is_critical', False) or any(model_anomalies.values())
            metrics.analysis_completed = True
            metrics.save()
            
            logger.info(f"Analyse LLM terminée pour {metrics.id} - Score: {severity_score}")
            return anomaly_detection
            
        except Exception as e:
            logger.error(f"Erreur analyse LLM métrique {metrics.id}: {e}")
            return None
    
    def _convert_llm_to_model_format(self, llm_analysis: Dict[str, Any]) -> Dict[str, bool]:
        """
        Convertit les anomalies LLM vers le format du modèle Django.
        
        Args:
            llm_analysis: Analyse LLM complète
            
        Returns:
            Dict: Anomalies au format modèle
        """
        llm_anomalies = llm_analysis.get('anomalies_detected', {})
        
        return {
            'cpu_anomaly': llm_anomalies.get('cpu', False),
            'memory_anomaly': llm_anomalies.get('memory', False),
            'latency_anomaly': llm_anomalies.get('latency', False),
            'disk_anomaly': llm_anomalies.get('disk', False),
            'io_anomaly': llm_anomalies.get('io', False),
            'error_rate_anomaly': llm_anomalies.get('error_rate', False),
            'temperature_anomaly': llm_anomalies.get('temperature', False),
            'power_anomaly': llm_anomalies.get('power', False),
            'service_anomaly': llm_anomalies.get('services', False)
        }
    
    def analyze_batch_metrics(self, metrics_queryset) -> Dict[str, int]:
        """
        Analyse un lot de métriques avec la méthode LLM.
        
        Args:
            metrics_queryset: QuerySet des métriques à analyser
            
        Returns:
            Dict: Statistiques d'analyse LLM
        """
        results = {
            'total': metrics_queryset.count(),
            'analyzed': 0,
            'errors': 0,
            'llm_available': 0
        }
        
        for metrics in metrics_queryset:
            try:
                anomaly_detection = self.analyze_metrics(metrics)
                if anomaly_detection:
                    results['analyzed'] += 1
                    
                    # Vérification si LLM a été utilisé
                    if 'LLM: ' in anomaly_detection.anomaly_summary:
                        results['llm_available'] += 1
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Erreur analyse lot LLM métrique {metrics.id}: {e}")
        
        logger.info(f"Analyse LLM lot terminée: {results['analyzed']}/{results['total']} succès")
        logger.info(f"LLM utilisé: {results['llm_available']}")
        
        return results
    
    @property
    def is_available(self) -> bool:
        """
        Vérifie la disponibilité du service LLM.
        
        Returns:
            bool: True si Azure OpenAI est disponible
        """
        return self.llm_engine.is_available