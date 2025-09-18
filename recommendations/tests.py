"""
Tests unitaires pour l'application de recommandations.
Tests des services de génération de recommandations classiques et LLM.
"""

import json
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from ingestion.models import InfrastructureMetrics
from recommendations.models import RecommendationReport
from recommendations.services.classic import ClassicRecommendationGenerator
from recommendations.services.llm import LLMRecommendationGenerator
from recommendations.services import RecommendationService
from recommendations.codes import ResponseCodes, ResponseMessages, APIResponse
from recommendations.filters import RecommendationFilters, MetricsFilters


class TestMetricsFilters(TestCase):
    """Tests pour les filtres des métriques."""
    
    def setUp(self):
        """Configuration des données de test."""
        # Métriques avec analyse terminée
        self.analyzed_metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=75.0,
            memory_usage=65.0,
            latency_ms=200,
            disk_usage=45.0,
            network_in_kbps=1000,
            network_out_kbps=800,
            io_wait=5.0,
            thread_count=50,
            active_connections=20,
            error_rate=0.01,
            uptime_seconds=86400,
            temperature_celsius=45.0,
            power_consumption_watts=200,
            service_status={'api': 'online', 'db': 'online'},
            analysis_completed=True,
            is_anomalous=True
        )
        
        # Métriques sans analyse
        self.unanalyzed_metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=45.0,
            memory_usage=50.0,
            latency_ms=150,
            disk_usage=40.0,
            network_in_kbps=800,
            network_out_kbps=600,
            io_wait=2.0,
            thread_count=30,
            active_connections=15,
            error_rate=0.005,
            uptime_seconds=172800,
            temperature_celsius=40.0,
            power_consumption_watts=180,
            service_status={'api': 'online', 'db': 'online'},
            analysis_completed=False,
            is_anomalous=False
        )
    
    def test_validate_metrics_id_valid(self):
        """Test validation d'ID valide."""
        # ID positif
        validated_id = MetricsFilters.validate_metrics_id('123')
        self.assertEqual(validated_id, 123)
        
        # ID avec chaîne numérique
        validated_id = MetricsFilters.validate_metrics_id('456')
        self.assertEqual(validated_id, 456)
    
    def test_validate_metrics_id_invalid(self):
        """Test validation d'ID invalide."""
        # ID négatif
        with self.assertRaises(ValueError):
            MetricsFilters.validate_metrics_id('-1')
        
        # ID zéro
        with self.assertRaises(ValueError):
            MetricsFilters.validate_metrics_id('0')
        
        # ID non numérique
        with self.assertRaises(ValueError):
            MetricsFilters.validate_metrics_id('abc')
        
        # ID vide
        with self.assertRaises(ValueError):
            MetricsFilters.validate_metrics_id('')
        
        # ID None
        with self.assertRaises(ValueError):
            MetricsFilters.validate_metrics_id(None)
    
    def test_validate_generation_method_valid(self):
        """Test validation de méthode valide."""
        # Méthode classique
        method = MetricsFilters.validate_generation_method('classic')
        self.assertEqual(method, 'classic')
        
        # Méthode LLM
        method = MetricsFilters.validate_generation_method('llm')
        self.assertEqual(method, 'llm')
    
    def test_validate_generation_method_invalid(self):
        """Test validation de méthode invalide."""
        # Méthode invalide - retourne 'classic' par défaut
        method = MetricsFilters.validate_generation_method('invalid')
        self.assertEqual(method, 'classic')
        
        # Méthode vide
        method = MetricsFilters.validate_generation_method('')
        self.assertEqual(method, 'classic')
        
        # Méthode None
        method = MetricsFilters.validate_generation_method(None)
        self.assertEqual(method, 'classic')
    
    def test_get_metrics_without_reports(self):
        """Test récupération des métriques sans rapport."""
        # Initialement, aucun rapport n'existe
        queryset = MetricsFilters.get_metrics_without_reports()
        
        # Seules les métriques analysées devraient être retournées
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.analyzed_metrics)
        
        # Créer un rapport pour les métriques analysées
        RecommendationReport.objects.create(
            metrics=self.analyzed_metrics,
            executive_summary="Test summary",
            detailed_analysis="Test analysis",
            recommendations_json={"actions": []},
            priority_level="medium",
            estimated_impact="moderate",
            implementation_timeframe="2-4 weeks"
        )
        
        # Maintenant, aucune métrique sans rapport ne devrait être retournée
        queryset = MetricsFilters.get_metrics_without_reports()
        self.assertEqual(queryset.count(), 0)
    
    def test_get_metrics_with_critical_anomalies(self):
        """Test récupération des métriques avec anomalies critiques."""
        # Créer des métriques avec anomalies critiques
        from ingestion.models import AnomalyDetection
        
        # Créer une détection d'anomalie critique
        critical_detection = AnomalyDetection.objects.create(
            metrics=self.analyzed_metrics,
            cpu_anomaly=True,
            memory_anomaly=True,
            severity_score=9  # Score >= 7 makes is_critical=True
        )
        
        queryset = MetricsFilters.get_metrics_with_critical_anomalies()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.analyzed_metrics)


class TestRecommendationFilters(TestCase):
    """Tests pour les filtres de recommandations."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.metrics1 = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=85.0,
            memory_usage=75.0,
            latency_ms=300,
            disk_usage=70.0,
            network_in_kbps=1200,
            network_out_kbps=900,
            io_wait=8.0,
            thread_count=80,
            active_connections=40,
            error_rate=0.02,
            uptime_seconds=86400,
            temperature_celsius=55.0,
            power_consumption_watts=250,
            service_status={'api': 'online', 'db': 'degraded'},
            analysis_completed=True
        )
        
        self.metrics2 = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=45.0,
            memory_usage=50.0,
            latency_ms=120,
            disk_usage=35.0,
            network_in_kbps=800,
            network_out_kbps=600,
            io_wait=2.0,
            thread_count=40,
            active_connections=20,
            error_rate=0.005,
            uptime_seconds=172800,
            temperature_celsius=40.0,
            power_consumption_watts=180,
            service_status={'api': 'online', 'db': 'online'},
            analysis_completed=True
        )
        
        # Rapport urgent et critique
        self.critical_report = RecommendationReport.objects.create(
            metrics=self.metrics1,
            executive_summary="Critical issues detected",
            detailed_analysis="System overloaded",
            recommendations_json={"actions": ["scale_up", "optimize"]},
            priority_level="critical",
            estimated_impact="high",
            implementation_timeframe="immediate",
            generation_method="classic",
            is_reviewed=False
        )
        
        # Rapport normal
        self.normal_report = RecommendationReport.objects.create(
            metrics=self.metrics2,
            executive_summary="Minor optimizations needed",
            detailed_analysis="System performing well",
            recommendations_json={"actions": ["monitor"]},
            priority_level="low",
            estimated_impact="low",
            implementation_timeframe="1-2 weeks",
            generation_method="llm",
            is_reviewed=True
        )
    
    def test_get_filtered_reports_no_filters(self):
        """Test récupération sans filtres."""
        queryset = RecommendationFilters.get_filtered_reports({})
        
        # Tous les rapports doivent être retournés, triés par date
        self.assertEqual(queryset.count(), 2)
        # Le plus récent en premier
        self.assertEqual(queryset.first().priority_level, 'low')  # normal_report créé en dernier
    
    def test_get_filtered_reports_priority_filter(self):
        """Test filtrage par priorité."""
        # Filtrer les rapports critiques
        queryset = RecommendationFilters.get_filtered_reports({'priority': 'critical'})
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.critical_report)
        
        # Filtrer les rapports de priorité faible
        queryset = RecommendationFilters.get_filtered_reports({'priority': 'low'})
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.normal_report)
        
        # Priorité inexistante
        queryset = RecommendationFilters.get_filtered_reports({'priority': 'nonexistent'})
        self.assertEqual(queryset.count(), 2)  # Filtre ignoré
    
    def test_get_filtered_reports_urgent_filter(self):
        """Test filtrage par urgence."""
        queryset = RecommendationFilters.get_filtered_reports({'urgent_only': 'true'})
        
        # Seul le rapport critique est urgent
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.critical_report)
        
        # Test avec différentes valeurs truthy
        for value in ['1', 'yes', 'True', 'TRUE']:
            queryset = RecommendationFilters.get_filtered_reports({'urgent_only': value})
            self.assertEqual(queryset.count(), 1)
    
    def test_get_filtered_reports_method_filter(self):
        """Test filtrage par méthode de génération."""
        # Filtrer méthode classique
        queryset = RecommendationFilters.get_filtered_reports({'method': 'classic'})
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.critical_report)
        
        # Filtrer méthode LLM
        queryset = RecommendationFilters.get_filtered_reports({'method': 'llm'})
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.normal_report)
    
    def test_get_filtered_reports_limit(self):
        """Test limitation du nombre de résultats."""
        queryset = RecommendationFilters.get_filtered_reports({'limit': '1'})
        self.assertEqual(len(queryset), 1)
        
        # Limite par défaut
        queryset = RecommendationFilters.get_filtered_reports({})
        self.assertLessEqual(len(queryset), 50)
        
        # Limite invalide - utilise la valeur par défaut
        queryset = RecommendationFilters.get_filtered_reports({'limit': 'invalid'})
        self.assertLessEqual(len(queryset), 50)
    
    def test_get_filter_info(self):
        """Test récupération des informations de filtrage."""
        query_params = {
            'priority': 'high',
            'urgent_only': 'true',
            'method': 'llm',
            'last_days': '7',
            'limit': '25'
        }
        
        filter_info = RecommendationFilters.get_filter_info(query_params)
        
        self.assertEqual(filter_info['priority'], 'high')
        self.assertTrue(filter_info['urgent_only'])
        self.assertEqual(filter_info['method'], 'llm')
        self.assertEqual(filter_info['last_days'], 7)
        self.assertEqual(filter_info['limit'], 25)
    
    def test_get_filter_info_invalid_last_days(self):
        """Test gestion des jours invalides."""
        query_params = {'last_days': 'invalid'}
        filter_info = RecommendationFilters.get_filter_info(query_params)
        
        # Les jours invalides sont ignorés
        self.assertNotIn('last_days', filter_info)


class TestAPIResponse(TestCase):
    """Tests pour les réponses API standardisées."""
    
    def test_success_response(self):
        """Test création réponse de succès."""
        response = APIResponse.success("Test message")
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], "Test message")
        self.assertEqual(response.data['code'], ResponseCodes.SUCCESS)
    
    def test_success_response_with_data(self):
        """Test réponse de succès avec données."""
        data = {'report_id': 123, 'count': 5}
        response = APIResponse.success("Success with data", data=data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['report_id'], 123)
        self.assertEqual(response.data['count'], 5)
    
    def test_error_response(self):
        """Test création réponse d'erreur."""
        response = APIResponse.error("Test error")
        
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], "Test error")
        self.assertEqual(response.data['error_code'], ResponseCodes.INTERNAL_ERROR)
    
    def test_error_response_with_details(self):
        """Test réponse d'erreur avec détails."""
        details = {'field': 'cpu_usage', 'value': 'invalid'}
        response = APIResponse.error("Validation failed", details=details)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['details'], details)
    
    def test_validation_error(self):
        """Test erreur de validation."""
        field_errors = {'metrics_id': 'Required field'}
        response = APIResponse.validation_error("Validation failed", field_errors)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_code'], ResponseCodes.INVALID_PARAMETERS)
        self.assertEqual(response.data['details']['field_errors'], field_errors)
    
    def test_not_found_response(self):
        """Test réponse ressource non trouvée."""
        # Test avec métrique
        response = APIResponse.not_found("Métrique", "123")
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error_code'], ResponseCodes.METRICS_NOT_FOUND)
        self.assertIn("Métrique non trouvée (ID: 123)", response.data['error'])
        
        # Test avec rapport
        response = APIResponse.not_found("Rapport", "456")
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error_code'], ResponseCodes.REPORT_NOT_FOUND)
    
    def test_generation_success_response(self):
        """Test réponse succès génération."""
        response = APIResponse.generation_success(
            metrics_id=123,
            report_id=456,
            recommendations_count=5,
            priority_level="high",
            is_urgent=True,
            processing_time=2.5,
            method_used="classic",
            method_info={"version": "1.0"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['metrics_id'], 123)
        self.assertEqual(response.data['report_id'], 456)
        self.assertEqual(response.data['recommendations_count'], 5)
        self.assertEqual(response.data['priority_level'], "high")
        self.assertTrue(response.data['is_urgent'])
        self.assertEqual(response.data['processing_duration_seconds'], 2.5)
        self.assertEqual(response.data['method_used'], "classic")
    
    def test_report_already_exists_response(self):
        """Test réponse rapport existant."""
        mock_report = Mock()
        mock_report.recommendations = ["action1", "action2"]
        mock_report.priority_level = "medium"
        mock_report.is_urgent = False
        mock_report.generated_at = timezone.now()
        mock_report.generation_method = "llm"
        mock_report.executive_summary = "Short summary"
        
        response = APIResponse.report_already_exists(
            metrics_id=123,
            report_id=456,
            report=mock_report
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], ResponseCodes.REPORT_ALREADY_EXISTS)
        self.assertEqual(response.data['metrics_id'], 123)
        self.assertEqual(response.data['report_id'], 456)
        self.assertEqual(response.data['recommendations_count'], 2)
    
    def test_handle_exception(self):
        """Test gestion des exceptions."""
        test_exception = ValueError("Test exception")
        response = APIResponse.handle_exception(test_exception, "Test context")
        
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error_code'], ResponseCodes.INTERNAL_ERROR)
        self.assertIn("Test context", response.data['error'])
        self.assertIn("Test exception", response.data['error'])
        self.assertEqual(response.data['details']['exception_type'], 'ValueError')


class TestRecommendationService(TestCase):
    """Tests pour le service principal de recommandations."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=75.0,
            memory_usage=65.0,
            latency_ms=200,
            disk_usage=50.0,
            network_in_kbps=1000,
            network_out_kbps=800,
            io_wait=4.0,
            thread_count=60,
            active_connections=25,
            error_rate=0.01,
            uptime_seconds=86400,
            temperature_celsius=45.0,
            power_consumption_watts=200,
            service_status={'api': 'online', 'db': 'online'},
            analysis_completed=True,
            is_anomalous=True
        )
    
    def test_service_initialization_classic(self):
        """Test initialisation avec méthode classique."""
        service = RecommendationService(method='classic')
        
        self.assertEqual(service.method, 'classic')
        self.assertIsInstance(service.generator, ClassicRecommendationGenerator)
    
    def test_service_initialization_llm(self):
        """Test initialisation avec méthode LLM."""
        service = RecommendationService(method='llm')
        
        self.assertEqual(service.method, 'llm')
        self.assertIsInstance(service.generator, LLMRecommendationGenerator)
    
    def test_service_initialization_invalid_method(self):
        """Test initialisation avec méthode invalide."""
        service = RecommendationService(method='invalid_method')
        
        # Devrait utiliser 'classic' par défaut
        self.assertEqual(service.method, 'classic')
        self.assertIsInstance(service.generator, ClassicRecommendationGenerator)
    
    @patch.object(ClassicRecommendationGenerator, 'generate_report')
    def test_generate_recommendation_report(self, mock_generate):
        """Test génération de rapport."""
        mock_report = Mock()
        mock_report.id = 123
        mock_generate.return_value = mock_report
        
        service = RecommendationService(method='classic')
        result = service.generate_recommendation_report(self.metrics)
        
        self.assertEqual(result, mock_report)
        mock_generate.assert_called_once_with(self.metrics)
    
    def test_generate_batch_reports(self):
        """Test génération en lot."""
        # Créer métriques supplémentaires
        metrics2 = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=45.0,
            memory_usage=50.0,
            latency_ms=150,
            disk_usage=40.0,
            network_in_kbps=800,
            network_out_kbps=600,
            io_wait=2.0,
            thread_count=40,
            active_connections=18,
            error_rate=0.005,
            uptime_seconds=172800,
            temperature_celsius=40.0,
            power_consumption_watts=180,
            service_status={'api': 'online', 'db': 'online'},
            analysis_completed=True,
            is_anomalous=False
        )
        
        metrics_queryset = InfrastructureMetrics.objects.all()
        
        with patch.object(RecommendationService, 'generate_recommendation_report') as mock_generate:
            # Simuler succès pour toutes les métriques
            mock_generate.return_value = Mock(id=123)
            
            service = RecommendationService(method='classic')
            results = service.generate_batch_reports(metrics_queryset)
            
            self.assertEqual(results['total'], 2)
            self.assertEqual(results['generated'], 2)
            self.assertEqual(results['errors'], 0)
            self.assertEqual(results['skipped'], 0)
    
    def test_generate_batch_reports_with_errors(self):
        """Test génération en lot avec erreurs."""
        metrics_queryset = InfrastructureMetrics.objects.filter(id=self.metrics.id)
        
        with patch.object(RecommendationService, 'generate_recommendation_report') as mock_generate:
            # Simuler une erreur
            mock_generate.side_effect = Exception("Generation failed")
            
            service = RecommendationService(method='classic')
            results = service.generate_batch_reports(metrics_queryset)
            
            self.assertEqual(results['total'], 1)
            self.assertEqual(results['generated'], 0)
            self.assertEqual(results['errors'], 1)
    
    def test_is_llm_available_classic_method(self):
        """Test disponibilité LLM avec méthode classique."""
        service = RecommendationService(method='classic')
        self.assertFalse(service.is_llm_available)
    
    def test_is_llm_available_llm_method(self):
        """Test disponibilité LLM avec méthode LLM."""
        with patch.object(LLMRecommendationGenerator, 'is_available', True):
            service = RecommendationService(method='llm')
            self.assertTrue(service.is_llm_available)
    
    def test_get_method_info(self):
        """Test récupération informations méthode."""
        service = RecommendationService(method='classic')
        info = service.get_method_info()
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['current_method'], 'classic')
        self.assertEqual(info['generator_class'], 'ClassicRecommendationGenerator')


class TestRecommendationModels(TestCase):
    """Tests pour les modèles de recommandations."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=85.0,
            memory_usage=75.0,
            latency_ms=300,
            disk_usage=70.0,
            network_in_kbps=1200,
            network_out_kbps=900,
            io_wait=8.0,
            thread_count=80,
            active_connections=40,
            error_rate=0.03,
            uptime_seconds=86400,
            temperature_celsius=55.0,
            power_consumption_watts=280,
            service_status={'api': 'online', 'db': 'degraded'},
            analysis_completed=True
        )
        
        self.report = RecommendationReport.objects.create(
            metrics=self.metrics,
            executive_summary="Critical performance issues detected",
            detailed_analysis="System showing signs of overload",
            recommendations_json={
                "actions": [
                    {"type": "scale", "priority": "high", "description": "Scale up instances"},
                    {"type": "optimize", "priority": "medium", "description": "Optimize queries"}
                ]
            },
            priority_level="critical",
            estimated_impact="high",
            implementation_timeframe="immediate",
            generation_method="classic"
        )
    
    def test_report_str_representation(self):
        """Test représentation string du rapport."""
        str_repr = str(self.report)
        self.assertIn("critical", str_repr)
        self.assertIn(self.metrics.timestamp.strftime('%Y-%m-%d'), str_repr)
    
    def test_total_recommendations_property(self):
        """Test propriété total_recommendations."""
        self.assertEqual(self.report.total_recommendations, 2)
        
        # Test avec recommendations_json vide
        self.report.recommendations_json = {}
        self.assertEqual(self.report.total_recommendations, 0)
        
        # Test avec recommendations_json non-dict
        self.report.recommendations_json = "not a dict"
        self.assertEqual(self.report.total_recommendations, 0)
    
    def test_is_urgent_property(self):
        """Test propriété is_urgent."""
        # Rapport critique - urgent
        self.assertTrue(self.report.is_urgent)
        
        # Rapport haute priorité - urgent
        self.report.priority_level = "high"
        self.assertTrue(self.report.is_urgent)
        
        # Rapport priorité moyenne - non urgent
        self.report.priority_level = "medium"
        self.assertFalse(self.report.is_urgent)
        
        # Rapport priorité faible - non urgent
        self.report.priority_level = "low"
        self.assertFalse(self.report.is_urgent)
    
    def test_recommendations_property(self):
        """Test propriété recommendations."""
        recommendations = self.report.recommendations
        self.assertEqual(len(recommendations), 2)
        self.assertEqual(recommendations[0]["type"], "scale")
        self.assertEqual(recommendations[1]["type"], "optimize")
        
        # Test avec recommendations_json vide
        self.report.recommendations_json = {}
        self.assertEqual(self.report.recommendations, [])
        
        # Test avec recommendations_json non-dict
        self.report.recommendations_json = "not a dict"
        self.assertEqual(self.report.recommendations, [])
