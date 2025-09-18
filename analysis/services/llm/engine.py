"""
Moteur d'analyse LLM pour Azure OpenAI.
Gère la connexion et les interactions avec l'API.
"""

import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from openai import AzureOpenAI
from .prompts import AnomalyAnalysisPrompts

logger = logging.getLogger(__name__)


class LLMAnalysisEngine:
    """
    Moteur d'analyse utilisant Azure OpenAI.
    Gère la configuration, les appels API et le parsing des réponses.
    """
    
    def __init__(self):
        self.azure_client = None
        self.prompts = AnomalyAnalysisPrompts()
        self._initialize_azure_client()
    
    def _initialize_azure_client(self) -> None:
        """
        Initialise le client Azure OpenAI avec gestion d'erreurs.
        """
        try:
            required_settings = [
                'AZURE_OPENAI_ENDPOINT',
                'AZURE_OPENAI_API_KEY', 
                'AZURE_OPENAI_DEPLOYMENT_NAME'
            ]
            
            missing_settings = [
                setting for setting in required_settings 
                if not getattr(settings, setting, None)
            ]
            
            if missing_settings:
                logger.debug(f"Configuration Azure OpenAI non configurée: {missing_settings}")
                return
            
            self.azure_client = AzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
            
            logger.info("Client Azure OpenAI initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur initialisation Azure OpenAI: {e}")
            self.azure_client = None
    
    def call_llm_analysis(self, prompt: str, analysis_type: str = "general") -> Optional[Dict[str, Any]]:
        """
        Effectue un appel générique à Azure OpenAI.
        
        Args:
            prompt: Prompt formaté pour l'analyse
            analysis_type: Type d'analyse pour le logging
            
        Returns:
            Dict: Réponse parsée ou None si erreur
        """
        if not self.azure_client:
            logger.debug(f"Azure OpenAI non configuré pour {analysis_type}")
            return None
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "Vous êtes un expert en infrastructure IT. Analysez avec précision et répondez uniquement en JSON valide."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            response = self.azure_client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=messages
            )
            
            # Extraction et nettoyage du contenu
            content = response.choices[0].message.content.strip()
            content = self._clean_json_response(content)
            
            # Parse JSON
            parsed_response = json.loads(content)
            
            logger.info(f"Analyse LLM {analysis_type} terminée avec succès")
            return parsed_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON pour {analysis_type}: {e}")
            logger.error(f"Contenu reçu: {content[:200]}...")
            return None
            
        except Exception as e:
            logger.error(f"Erreur appel LLM {analysis_type}: {e}")
            return None
    
    def _clean_json_response(self, content: str) -> str:
        """
        Nettoie la réponse LLM pour extraire le JSON valide.
        
        Args:
            content: Réponse brute du LLM
            
        Returns:
            str: JSON nettoyé
        """
        # Suppression des markdown blocks
        if content.startswith('```json'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        
        if content.endswith('```'):
            content = content[:-3]
        
        # Suppression des espaces et retours à la ligne en trop
        content = content.strip()
        
        return content
    
    def detect_anomalies(self, metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Détecte les anomalies via LLM.
        
        Args:
            metrics_data: Données des métriques formatées
            
        Returns:
            Dict: Analyse des anomalies ou None
        """
        prompt = self.prompts.get_anomaly_detection_prompt(metrics_data)
        return self.call_llm_analysis(prompt, "anomaly_detection")
    
    def assess_severity(self, metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Évalue la sévérité via LLM.
        
        Args:
            metrics_data: Données complètes des métriques
            
        Returns:
            Dict: Évaluation de sévérité ou None
        """
        prompt = self.prompts.get_severity_assessment_prompt(metrics_data)
        return self.call_llm_analysis(prompt, "severity_assessment")
    
    def analyze_correlations(self, metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyse les corrélations via LLM.
        
        Args:
            metrics_data: Données des métriques
            
        Returns:
            Dict: Analyse des corrélations ou None
        """
        prompt = self.prompts.get_correlation_analysis_prompt(metrics_data)
        return self.call_llm_analysis(prompt, "correlation_analysis")
    
    @property
    def is_available(self) -> bool:
        """
        Vérifie la disponibilité du service LLM.
        
        Returns:
            bool: True si Azure OpenAI est disponible
        """
        return self.azure_client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du moteur LLM.
        
        Returns:
            Dict: Informations de statut
        """
        return {
            'azure_openai_configured': self.is_available,
            'endpoint': getattr(settings, 'AZURE_OPENAI_ENDPOINT', None),
            'deployment': getattr(settings, 'AZURE_OPENAI_DEPLOYMENT_NAME', None),
            'api_version': "2024-02-01"
        }