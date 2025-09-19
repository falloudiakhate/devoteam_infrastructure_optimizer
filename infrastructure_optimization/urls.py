"""
Configuration des URLs pour le projet infrastructure_optimization.

Intègre la documentation Swagger via drf-yasg et route vers
les apps spécialisées (ingestion, analysis, recommendations).
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuration de la documentation Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Infrastructure Optimization API",
        default_version='v1',
        description="""
        API complète pour l'optimisation d'infrastructure.
        
        ## Architecture
        - **Ingestion** : Collecte et traitement des métriques d'infrastructure
        - **Analysis** : Détection d'anomalies avec machine learning
        - **Recommendations** : Génération de recommandations avec Azure OpenAI
        
        ## Authentification
        Actuellement en mode développement sans authentification requise.
        
        ## Formats de données
        - JSON pour tous les échanges de données
        - ISO 8601 pour les timestamps
        - Pagination automatique pour les listes
        
        ## Versions supportées
        - Python 3.10+
        - Django 5.2
        - Django REST Framework 3.15+
        """,
        terms_of_service="https://devoteam.com/terms/",
        contact=openapi.Contact(email="infrastructure@devoteam.com"),
        license=openapi.License(name="Propriétaire Devoteam"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url='https://infrastructure-optimizer-gqg3g0d5fraqdmdb.francecentral-01.azurewebsites.net',
)

urlpatterns = [
    # Interface d'administration Django
    path('admin', admin.site.urls),
    
    # Documentation API Swagger/OpenAPI
    path('swagger<format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # APIs spécialisées par domaine métier
    path('api/ingestion/', include('ingestion.urls')),
    path('api/analysis/', include('analysis.urls')),
    path('api/recommendations/', include('recommendations.urls')),
    
    # Interface utilisateur frontend
    path('', include('frontend.urls')),
    
    # Interface utilisateur simple (redirection vers dashboard)
    path('', TemplateView.as_view(template_name='frontend/index.html'), name='home'),
]
