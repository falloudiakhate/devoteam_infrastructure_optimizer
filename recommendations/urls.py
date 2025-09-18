from django.urls import path
from .views import (
    RecommendationGenerationView,
    RecommendationResultView,
    RecommendationListView
)

urlpatterns = [
    # Génération de recommandations (unique ou en lot)
    path('generate', RecommendationGenerationView.as_view(), name='generate-recommendations'),
    
    # Récupération d'un rapport spécifique
    path('reports/<int:report_id>', RecommendationResultView.as_view(), name='recommendation-report'),
    
    # Liste des rapports avec filtres
    path('reports', RecommendationListView.as_view(), name='recommendation-reports-list'),
]

