"""
Prompts pour l'analyse d'anomalies via LLM.
Templates et configurations pour Azure OpenAI.
"""

import json
from typing import Dict, Any


class AnomalyAnalysisPrompts:
    """
    Collection de prompts optimisés pour l'analyse d'anomalies via LLM.
    """
    
    @staticmethod
    def get_anomaly_detection_prompt(metrics_data: Dict[str, Any]) -> str:
        """
        Génère un prompt pour la détection d'anomalies.
        
        Args:
            metrics_data: Données des métriques à analyser
            
        Returns:
            str: Prompt formaté pour l'analyse LLM
        """
        return f"""
        Vous êtes un expert en infrastructure IT. Analysez ces métriques système pour détecter les anomalies :

        MÉTRIQUES SYSTÈME :
        {json.dumps(metrics_data, indent=2)}

        MISSION D'ANALYSE :
        1. Identifiez les métriques anormales avec justifications
        2. Évaluez le niveau de sévérité (1-10)
        3. Détectez les corrélations suspectes entre métriques
        4. Estimez l'impact sur les performances
        5. Déterminez l'urgence d'intervention

        CONTEXTE OPÉRATIONNEL :
        - Infrastructure de production critique
        - Haute disponibilité requise
        - Détection proactive prioritaire
        - Tolérance minimale aux pannes

        RÉPONSE JSON ATTENDUE :
        {{
            "anomalies_detected": {{
                "cpu": boolean,
                "memory": boolean,
                "disk": boolean,
                "latency": boolean,
                "io": boolean,
                "error_rate": boolean,
                "temperature": boolean,
                "power": boolean,
                "services": boolean
            }},
            "severity_score": integer_entre_1_et_10,
            "ai_confidence": float_entre_0_et_1,
            "anomaly_explanations": ["explication1", "explication2"],
            "correlations_found": ["corrélation1", "corrélation2"],
            "risk_assessment": "évaluation_du_risque_principal",
            "is_critical": boolean,
            "recommended_actions": ["action1", "action2"]
        }}

        IMPORTANT : Répondez UNIQUEMENT avec le JSON, aucun autre texte.
        """
    
    @staticmethod
    def get_severity_assessment_prompt(metrics_data: Dict[str, Any]) -> str:
        """
        Prompt spécialisé pour l'évaluation de sévérité.
        
        Args:
            metrics_data: Données complètes des métriques
            
        Returns:
            str: Prompt d'évaluation de sévérité
        """
        return f"""
        Expert infrastructure, évaluez précisément la sévérité de cette situation système :

        DONNÉES COMPLÈTES :
        {json.dumps(metrics_data, indent=2)}

        CRITÈRES D'ÉVALUATION :
        1. Impact immédiat utilisateurs (0-3 points)
        2. Risque d'effet domino (0-2 points)
        3. Dégradation progressive vs panne (0-2 points)
        4. Criticité services affectés (0-3 points)

        JSON DE RÉPONSE :
        {{
            "severity_score": integer_1_à_10,
            "severity_justification": "explication_détaillée",
            "immediate_risk": boolean,
            "cascade_risk": boolean,
            "business_impact": "faible|modéré|élevé|critique",
            "time_to_failure": "estimation_en_minutes_ou_heures"
        }}
        """
    
    @staticmethod
    def get_correlation_analysis_prompt(metrics_data: Dict[str, Any]) -> str:
        """
        Prompt pour l'analyse des corrélations entre métriques.
        
        Args:
            metrics_data: Données des métriques
            
        Returns:
            str: Prompt d'analyse de corrélations
        """
        return f"""
        Analysez les corrélations et patterns dans ces métriques système :

        MÉTRIQUES :
        {json.dumps(metrics_data, indent=2)}

        ANALYSE DEMANDÉE :
        1. Corrélations fortes entre métriques
        2. Relations causales détectées
        3. Patterns anormaux de comportement
        4. Corrélations manquantes (attendues mais absentes)

        RÉPONSE JSON :
        {{
            "strong_correlations": [
                {{
                    "metrics_pair": ["métrique1", "métrique2"],
                    "correlation_strength": "forte|modérée|faible",
                    "correlation_type": "positive|négative|causale",
                    "explanation": "justification_de_la_corrélation"
                }}
            ],
            "anomalous_patterns": ["pattern1", "pattern2"],
            "missing_correlations": ["corrélation_attendue_manquante"],
            "insights": ["insight1", "insight2"]
        }}
        """
    
    @staticmethod
    def get_system_parameters() -> Dict[str, Any]:
        """
        Paramètres système pour les requêtes LLM.
        
        Returns:
            Dict: Configuration optimale pour l'analyse
        """
        return {
            'temperature': 0.1  # Très peu de créativité, maximum de précision
        }
    
    @staticmethod
    def get_fallback_response(severity_score: int = 5) -> Dict[str, Any]:
        """
        Réponse de fallback en cas d'indisponibilité LLM.
        
        Args:
            severity_score: Score de sévérité par défaut
            
        Returns:
            Dict: Réponse compatible avec le format LLM
        """
        return {
            'anomalies_detected': {
                'cpu': False,
                'memory': False,
                'disk': False,
                'latency': False,
                'io': False,
                'error_rate': False,
                'temperature': False,
                'power': False,
                'services': False
            },
            'severity_score': severity_score,
            'ai_confidence': 0.0,
            'anomaly_explanations': ['Analyse LLM non disponible'],
            'correlations_found': [],
            'risk_assessment': 'Azure OpenAI temporairement indisponible',
            'is_critical': False,
            'recommended_actions': ['Utiliser analyse classique par seuils']
        }