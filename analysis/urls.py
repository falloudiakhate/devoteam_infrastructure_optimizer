from django.urls import path
from .views import AnomalyAnalysisView, AnomalyResultView, AnomalyListView



urlpatterns = [
    # Endpoint d'analyse
    path('analyze', AnomalyAnalysisView.as_view(), name='analyze'),
    # Endpoint pour récupérer une analyse existante
    path('result/<int:analysis_id>', AnomalyResultView.as_view(), name='result'),
    # Endpoint pour lister toutes les anomalies
    path('anomalies', AnomalyListView.as_view(), name='anomalies'),
]

