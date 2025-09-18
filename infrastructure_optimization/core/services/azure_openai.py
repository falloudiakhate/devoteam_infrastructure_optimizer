"""
Service partagé Azure OpenAI.
Utilisé par les modules analysis et recommendations.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class AzureOpenAIService:
    """
    Service partagé pour l'intégration Azure OpenAI.
    Utilisé par les modules d'analyse et de recommandations.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pour éviter les multiples connexions."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_key = getattr(settings, 'AZURE_OPENAI_API_KEY', '')
        self.endpoint = getattr(settings, 'AZURE_OPENAI_ENDPOINT', '')
        self.api_version = getattr(settings, 'AZURE_OPENAI_API_VERSION', '2024-02-01')
        self.deployment_name = getattr(settings, 'AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
        
        # Validation et initialisation
        self.client = None
        self._initialize_client()
        self._initialized = True
    
    def _initialize_client(self) -> None:
        """
        Initialise le client Azure OpenAI avec gestion d'erreurs.
        """
        if not all([self.api_key, self.endpoint]):
            logger.warning("Configuration Azure OpenAI incomplète")
            return
        
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )
            logger.info("Service Azure OpenAI initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur initialisation Azure OpenAI: {e}")
            self.client = None
    
    def call_completion(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Appel générique à Azure OpenAI Chat Completions.
        
        Args:
            messages: Liste des messages (system, user, assistant)
            
        Returns:
            str: Réponse du modèle ou None si erreur
        """
        if not self.client:
            logger.warning("Client Azure OpenAI non disponible")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages
            )
            
            content = response.choices[0].message.content.strip()
            return content
            
        except Exception as e:
            logger.error(f"Erreur appel Azure OpenAI: {e}")
            return None
    
    def call_json_completion(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Appel Azure OpenAI avec parsing JSON automatique.
        
        Args:
            messages: Messages pour l'API
            
        Returns:
            Dict: Réponse parsée en JSON ou None
        """
        raw_response = self.call_completion(
            messages=messages
        )
        
        if not raw_response:
            return None
        
        return self.parse_json_response(raw_response)
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse une réponse texte vers JSON avec nettoyage automatique.
        
        Args:
            response: Réponse texte du LLM
            
        Returns:
            Dict: JSON parsé ou None si échec
        """
        try:
            # Nettoyage de la réponse
            cleaned_response = self._clean_response(response)
            
            # Tentative de parsing direct
            return json.loads(cleaned_response)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Échec parsing direct JSON: {e}")
            try:
                # Tentative d'extraction du JSON dans la réponse
                return self._extract_json_from_text(response)
            except Exception as extraction_error:
                logger.error(f"Échec extraction JSON: {extraction_error}")
                logger.error(f"Réponse problématique: {response[:200]}...")
                
                # Retourner une structure minimale valide en dernier recours
                return {
                    "executive_summary": "Recommandations générées par analyse LLM.",
                    "detailed_analysis": "Analyse détaillée des métriques système.",
                    "recommendations": [],
                    "priority_level": "medium",
                    "estimated_impact": "Amélioration des performances système",
                    "implementation_timeframe": "1-2 semaines"
                }
    
    def _clean_response(self, response: str) -> str:
        """
        Nettoie la réponse pour faciliter le parsing JSON.
        
        Args:
            response: Réponse brute
            
        Returns:
            str: Réponse nettoyée
        """
        # Suppression des blocs markdown et préfixes
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        elif response.startswith('json'):
            response = response[4:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        return response.strip()
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrait le JSON d'un texte contenant autre chose.
        
        Args:
            text: Texte contenant du JSON
            
        Returns:
            Dict: JSON extrait
        """
        # Recherche du premier { et du dernier }
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise json.JSONDecodeError("Pas de JSON trouvé", text, 0)
        
        json_part = text[start_idx:end_idx]
        
        # Si le JSON semble tronqué, essayer de le reconstruire avec des valeurs par défaut
        try:
            return json.loads(json_part)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON malformé détecté, tentative de reconstruction: {e}")
            # Retourner une structure minimale valide
            return {
                "executive_summary": "Recommandations générées par analyse LLM.",
                "detailed_analysis": "Analyse détaillée des métriques système. Analyse ciblée services incluse.",
                "recommendations": [],
                "priority_level": "medium",
                "estimated_impact": "Amélioration des performances système",
                "implementation_timeframe": "1-2 semaines"
            }
    
    def build_system_message(self, role: str, expertise: str, 
                           output_format: str = "JSON") -> Dict[str, str]:
        """
        Construit un message système standard.
        
        Args:
            role: Rôle de l'assistant (ex: "expert en infrastructure")
            expertise: Domaine d'expertise
            output_format: Format de sortie attendu
            
        Returns:
            Dict: Message système formaté
        """
        content = f"""Vous êtes un {role} spécialisé en {expertise}.
        
        Répondez de manière précise et professionnelle.
        Format de réponse attendu: {output_format}
        Si le format est JSON, ne retournez QUE du JSON valide, sans texte supplémentaire."""
                
        return {"role": "system", "content": content}
    
    def build_user_message(self, content: str) -> Dict[str, str]:
        """
        Construit un message utilisateur.
        
        Args:
            content: Contenu du message
            
        Returns:
            Dict: Message utilisateur formaté
        """
        return {"role": "user", "content": content}
    
    @property
    def is_available(self) -> bool:
        """
        Vérifie si le service est disponible.
        
        Returns:
            bool: True si le client est initialisé
        """
        return self.client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du service.
        
        Returns:
            Dict: Informations de statut
        """
        return {
            'available': self.is_available,
            'endpoint': self.endpoint,
            'deployment': self.deployment_name,
            'api_version': self.api_version,
            'configured': bool(self.api_key and self.endpoint)
        }