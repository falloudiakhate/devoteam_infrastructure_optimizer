"""
Services partagés pour l'ensemble de l'application.
Contient les services communs utilisés par plusieurs modules.
"""

from .azure_openai import AzureOpenAIService

__all__ = ['AzureOpenAIService']