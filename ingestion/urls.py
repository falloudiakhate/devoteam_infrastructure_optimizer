from django.urls import path
from .views import DataIngestionView, BulkIngestionView, MetricsListView

urlpatterns = [
    # Endpoint d'ingestion unique (single et batch)
    path('ingest', DataIngestionView.as_view(), name='data-ingestion'),
    
    # Endpoint optimisé pour l'ingestion en lot
    path('bulk_ingestion', BulkIngestionView.as_view(), name='bulk-ingestion'),
    
    # Endpoint pour récupérer la liste des métriques
    path('metrics', MetricsListView.as_view(), name='metrics-list'),
]

