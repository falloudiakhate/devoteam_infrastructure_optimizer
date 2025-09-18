"""
URLs pour l'interface frontend.
"""

from django.urls import path
from .views import DashboardView, SimpleDashboardView, DashboardStatsView, QuickTestView, SystemHealthView

urlpatterns = [
    # Dashboard simplifié (par défaut)
    path('', SimpleDashboardView.as_view(), name='simple-dashboard'),
    
    # Dashboard complexe (ancien)
    path('complex/', DashboardView.as_view(), name='dashboard'),
    
    # API pour les statistiques
    path('api/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # Test rapide avec données d'exemple
    path('api/quick-test/', QuickTestView.as_view(), name='quick-test'),
    
    # État de santé du système
    path('api/health/', SystemHealthView.as_view(), name='system-health'),
]