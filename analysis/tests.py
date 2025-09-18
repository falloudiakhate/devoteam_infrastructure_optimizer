"""
Tests unitaires pour l'application d'analyse d'anomalies.
Tests des services de détection d'anomalies classiques et LLM.
"""

import json
from unittest.mock import Mock, patch
from django.test import TestCase
from django.utils import timezone

from ingestion.models import InfrastructureMetrics, AnomalyDetection
from analysis.services.classic.detector import ClassicAnomalyDetector
from analysis.services.llm.detector import LLMAnomalyDetector
from analysis.services.llm.engine import LLMAnalysisEngine
from analysis.services.llm.prompts import AnomalyAnalysisPrompts
from analysis.services import AnomalyDetectionService


class TestClassicAnomalyDetector(TestCase):
    """Tests pour le détecteur d'anomalies classique."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.detector = ClassicAnomalyDetector()
        
        # Métriques normales
        self.normal_metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=45.0,
            memory_usage=50.0,
            latency_ms=100,
            disk_usage=40.0,
            network_in_kbps=1000,
            network_out_kbps=800,
            io_wait=2.0,
            thread_count=50,
            active_connections=20,
            error_rate=0.001,
            uptime_seconds=86400,
            temperature_celsius=45.0,
            power_consumption_watts=200,
            service_status={'api': 'online', 'db': 'online'}
        )
        
        # Métriques avec anomalies
        self.anomalous_metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=95.0,  # Anomalie CPU
            memory_usage=90.0,  # Anomalie mémoire
            latency_ms=800,  # Anomalie latence
            disk_usage=95.0,  # Anomalie disque
            network_in_kbps=3000,
            network_out_kbps=2500,
            io_wait=25.0,  # Anomalie IO
            thread_count=200,
            active_connections=100,
            error_rate=0.1,  # Anomalie taux d'erreur
            uptime_seconds=86400,
            temperature_celsius=85.0,  # Anomalie température
            power_consumption_watts=450,  # Anomalie consommation
            service_status={'api': 'error', 'db': 'offline'}  # Anomalie services
        )
    
    def test_threshold_configuration(self):
        """Test configuration des seuils."""
        # Vérifier que les seuils par défaut existent
        self.assertIsInstance(self.detector.thresholds, dict)
        
        # Vérifier quelques seuils clés
        self.assertIn('cpu_usage', self.detector.thresholds)
        self.assertIn('memory_usage', self.detector.thresholds)
        self.assertIn('latency_ms', self.detector.thresholds)
        
        # Test modification des seuils
        self.detector.thresholds['cpu_usage'] = 70
        self.assertEqual(self.detector.thresholds['cpu_usage'], 70)
    
    def test_severity_score_calculation(self):
        """Test calcul du score de sévérité."""
        # Aucune anomalie
        no_anomalies = {
            'cpu_anomaly': False,
            'memory_anomaly': False,
            'latency_anomaly': False,
            'disk_anomaly': False,
            'io_anomaly': False,
            'error_rate_anomaly': False,
            'temperature_anomaly': False,
            'power_anomaly': False,
            'service_anomaly': False
        }
        severity = self.detector.calculate_severity_score(no_anomalies)
        self.assertEqual(severity, 0)
        
        # Quelques anomalies
        some_anomalies = {
            'cpu_anomaly': True,
            'memory_anomaly': True,
            'latency_anomaly': False,
            'disk_anomaly': False,
            'io_anomaly': False,
            'error_rate_anomaly': True,
            'temperature_anomaly': False,
            'power_anomaly': False,
            'service_anomaly': False
        }
        severity = self.detector.calculate_severity_score(some_anomalies)
        self.assertGreater(severity, 5)
        self.assertLess(severity, 8)
        
        # Toutes les anomalies
        all_anomalies = {
            'cpu_anomaly': True,
            'memory_anomaly': True,
            'latency_anomaly': True,
            'disk_anomaly': True,
            'io_anomaly': True,
            'error_rate_anomaly': True,
            'temperature_anomaly': True,
            'power_anomaly': True,
            'service_anomaly': True
        }
        severity = self.detector.calculate_severity_score(all_anomalies)
        self.assertEqual(severity, 10)
    
    def test_analyze_normal_metrics(self):
        """Test analyse complète de métriques normales."""
        result = self.detector.analyze_metrics(self.normal_metrics)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, AnomalyDetection)
        
        # Vérifier qu'aucune anomalie n'est détectée
        self.assertFalse(result.cpu_anomaly)
        self.assertFalse(result.memory_anomaly)
        self.assertFalse(result.latency_anomaly)
        self.assertFalse(result.disk_anomaly)
        self.assertFalse(result.io_anomaly)
        self.assertFalse(result.error_rate_anomaly)
        self.assertFalse(result.temperature_anomaly)
        self.assertFalse(result.power_anomaly)
        self.assertFalse(result.service_anomaly)
        
        # Score de sévérité faible
        self.assertLessEqual(result.severity_score, 3)
        self.assertFalse(result.is_critical)
        self.assertEqual(result.analysis_method, 'classic')
        
        # Vérification que les métriques sont mises à jour
        self.normal_metrics.refresh_from_db()
        self.assertTrue(self.normal_metrics.analysis_completed)
        self.assertFalse(self.normal_metrics.is_anomalous)
    
    def test_analyze_anomalous_metrics(self):
        """Test analyse complète de métriques avec anomalies."""
        result = self.detector.analyze_metrics(self.anomalous_metrics)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, AnomalyDetection)
        
        # Vérifier que les anomalies sont détectées
        self.assertTrue(result.cpu_anomaly)
        self.assertTrue(result.memory_anomaly)
        self.assertTrue(result.latency_anomaly)
        self.assertTrue(result.disk_anomaly)
        self.assertTrue(result.io_anomaly)
        self.assertTrue(result.error_rate_anomaly)
        self.assertTrue(result.temperature_anomaly)
        self.assertTrue(result.power_anomaly)
        self.assertTrue(result.service_anomaly)
        
        # Score de sévérité élevé
        self.assertGreaterEqual(result.severity_score, 8)
        self.assertTrue(result.is_critical)
        self.assertEqual(result.analysis_method, 'classic')
        
        # Vérification du résumé
        self.assertIn('critique', result.anomaly_summary.lower())
        
        # Vérification que les métriques sont mises à jour
        self.anomalous_metrics.refresh_from_db()
        self.assertTrue(self.anomalous_metrics.analysis_completed)
        self.assertTrue(self.anomalous_metrics.is_anomalous)
    
    def test_batch_analysis(self):
        """Test analyse en lot."""
        metrics_queryset = InfrastructureMetrics.objects.all()
        results = self.detector.analyze_batch_metrics(metrics_queryset)
        
        self.assertEqual(results['total'], 2)
        self.assertEqual(results['analyzed'], 2)
        self.assertEqual(results['errors'], 0)


class TestLLMAnalysisEngine(TestCase):
    """Tests pour le moteur d'analyse LLM."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.engine = LLMAnalysisEngine()
        
        self.sample_metrics_data = {
            'timestamp': '2023-10-01T12:00:00Z',
            'cpu_usage': 85.0,
            'memory_usage': 75.0,
            'latency_ms': 300,
            'disk_usage': 70.0,
            'error_rate': 0.05
        }
    
    def test_clean_json_response(self):
        """Test nettoyage des réponses JSON."""
        # Test avec blocs markdown
        markdown_json = '```json\n{"test": "value"}\n```'
        cleaned = self.engine._clean_json_response(markdown_json)
        self.assertEqual(cleaned, '{"test": "value"}')
        
        # Test avec blocs markdown sans spécifier json
        markdown_simple = '```\n{"test": "value"}\n```'
        cleaned = self.engine._clean_json_response(markdown_simple)
        self.assertEqual(cleaned, '{"test": "value"}')
        
        # Test réponse normale
        normal_json = '{"test": "value"}'
        cleaned = self.engine._clean_json_response(normal_json)
        self.assertEqual(cleaned, '{"test": "value"}')
        
        # Test avec espaces
        spaced_json = '  {"test": "value"}  '
        cleaned = self.engine._clean_json_response(spaced_json)
        self.assertEqual(cleaned, '{"test": "value"}')
    
    @patch('analysis.services.llm.engine.AzureOpenAI')
    @patch('django.conf.settings')
    def test_azure_client_initialization_success(self, mock_settings, mock_azure):
        """Test initialisation réussie du client Azure OpenAI."""
        # Configuration complète
        mock_settings.AZURE_OPENAI_ENDPOINT = 'https://test.openai.azure.com'
        mock_settings.AZURE_OPENAI_API_KEY = 'test-key'
        mock_settings.AZURE_OPENAI_DEPLOYMENT_NAME = 'gpt-4'
        mock_settings.AZURE_OPENAI_API_VERSION = '2024-02-01'
        
        engine = LLMAnalysisEngine()
        
        # Vérifier que le client est initialisé
        mock_azure.assert_called_once()
        self.assertTrue(engine.is_available)
    
    @patch('analysis.services.llm.engine.getattr')
    def test_azure_client_initialization_failure(self, mock_getattr):
        """Test échec initialisation client Azure OpenAI."""
        # Configuration manquante - simuler que getattr retourne None
        mock_getattr.return_value = None
        
        engine = LLMAnalysisEngine()
        
        # Vérifier que le client n'est pas initialisé
        self.assertIsNone(engine.azure_client)
        self.assertFalse(engine.is_available)
    
    @patch.object(LLMAnalysisEngine, 'call_llm_analysis')
    def test_detect_anomalies(self, mock_call):
        """Test détection d'anomalies via LLM."""
        mock_response = {
            'anomalies_detected': {
                'cpu': True,
                'memory': False,
                'latency': True,
                'disk': False
            },
            'severity_score': 7,
            'ai_confidence': 0.85,
            'is_critical': True,
            'risk_assessment': 'Charge CPU et latence élevées'
        }
        mock_call.return_value = mock_response
        
        result = self.engine.detect_anomalies(self.sample_metrics_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_response)
        # Vérifier que l'appel a été fait avec le bon type d'analyse
        self.assertTrue(mock_call.called)
    
    @patch.object(LLMAnalysisEngine, 'call_llm_analysis')
    def test_assess_severity(self, mock_call):
        """Test évaluation de sévérité via LLM."""
        mock_response = {
            'severity_score': 8,
            'severity_justification': 'CPU saturé et latence dégradée',
            'immediate_risk': True,
            'cascade_risk': False,
            'business_impact': 'élevé'
        }
        mock_call.return_value = mock_response
        
        result = self.engine.assess_severity(self.sample_metrics_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_response)
        # Vérifier que l'appel a été fait avec le bon type d'analyse
        self.assertTrue(mock_call.called)
    
    @patch.object(LLMAnalysisEngine, 'call_llm_analysis')
    def test_analyze_correlations(self, mock_call):
        """Test analyse de corrélations via LLM."""
        mock_response = {
            'strong_correlations': [
                {
                    'metrics_pair': ['cpu_usage', 'latency_ms'],
                    'correlation_strength': 'forte',
                    'correlation_type': 'positive',
                    'explanation': 'Charge CPU élevée impacte la latence'
                }
            ],
            'insights': ['CPU et latence corrélés']
        }
        mock_call.return_value = mock_response
        
        result = self.engine.analyze_correlations(self.sample_metrics_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_response)
        # Vérifier que l'appel a été fait avec le bon type d'analyse
        self.assertTrue(mock_call.called)
    
    def test_get_status(self):
        """Test récupération du statut du moteur."""
        status = self.engine.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('azure_openai_configured', status)
        self.assertIn('endpoint', status)
        self.assertIn('deployment', status)
        self.assertIn('api_version', status)
        
        # Vérifier le format de la version API
        self.assertEqual(status['api_version'], '2024-02-01')


class TestLLMAnomalyDetector(TestCase):
    """Tests pour le détecteur d'anomalies LLM."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.detector = LLMAnomalyDetector()
        
        self.metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=85.0,
            memory_usage=70.0,
            latency_ms=300,
            disk_usage=65.0,
            network_in_kbps=1500,
            network_out_kbps=1200,
            io_wait=8.0,
            thread_count=150,
            active_connections=60,
            error_rate=0.03,
            uptime_seconds=345600,  # 4 jours
            temperature_celsius=65.0,
            power_consumption_watts=280,
            service_status={'api': 'online', 'db': 'degraded'}
        )
    
    def test_prepare_metrics_data(self):
        """Test préparation des données métriques."""
        prepared_data = self.detector._prepare_metrics_data(self.metrics)
        
        # Vérifier que toutes les métriques sont incluses
        expected_keys = [
            'timestamp', 'cpu_usage', 'memory_usage', 'latency_ms',
            'disk_usage', 'network_in_kbps', 'network_out_kbps',
            'io_wait', 'thread_count', 'active_connections',
            'error_rate', 'uptime_hours', 'temperature_celsius',
            'power_consumption_watts', 'service_status', 'has_degraded_services'
        ]
        
        for key in expected_keys:
            self.assertIn(key, prepared_data)
        
        # Vérifier les valeurs
        self.assertEqual(prepared_data['cpu_usage'], 85.0)
        self.assertEqual(prepared_data['memory_usage'], 70.0)
        self.assertEqual(prepared_data['latency_ms'], 300)
        self.assertTrue(prepared_data['has_degraded_services'])  # db est dégradé
        
        # Vérifier la conversion uptime
        expected_uptime_hours = 345600 / 3600  # 96 heures
        self.assertEqual(prepared_data['uptime_hours'], expected_uptime_hours)
    
    def test_convert_llm_to_model_format(self):
        """Test conversion format LLM vers modèle Django."""
        llm_analysis = {
            'anomalies_detected': {
                'cpu': True,
                'memory': False,
                'latency': True,
                'disk': False,
                'io': True,
                'error_rate': False,
                'temperature': True,
                'power': False,
                'services': True
            }
        }
        
        model_format = self.detector._convert_llm_to_model_format(llm_analysis)
        
        # Vérifier la conversion
        self.assertTrue(model_format['cpu_anomaly'])
        self.assertFalse(model_format['memory_anomaly'])
        self.assertTrue(model_format['latency_anomaly'])
        self.assertFalse(model_format['disk_anomaly'])
        self.assertTrue(model_format['io_anomaly'])
        self.assertFalse(model_format['error_rate_anomaly'])
        self.assertTrue(model_format['temperature_anomaly'])
        self.assertFalse(model_format['power_anomaly'])
        self.assertTrue(model_format['service_anomaly'])
    
    def test_generate_llm_summary(self):
        """Test génération du résumé LLM."""
        llm_analysis = {
            'risk_assessment': 'Charge système élevée détectée',
            'anomaly_explanations': [
                'CPU saturé à 85%',
                'Latence dégradée à 300ms',
                'Services partiellement indisponibles'
            ],
            'correlations_found': [
                'CPU-Latence: corrélation forte',
                'Services-Erreurs: impact cascade'
            ],
            'is_critical': True,
            'recommended_actions': [
                'Redémarrer les services dégradés',
                'Optimiser les requêtes lentes'
            ]
        }
        
        summary = self.detector.generate_llm_summary(llm_analysis, self.metrics)
        
        # Vérifier que le résumé contient les éléments clés
        self.assertIn('Charge système élevée', summary)
        self.assertIn('CPU saturé', summary)
        self.assertIn('CPU-Latence', summary)
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)
    
    def test_generate_llm_summary_minimal(self):
        """Test génération résumé avec données minimales."""
        minimal_analysis = {
            'risk_assessment': 'Azure OpenAI temporairement indisponible',
            'anomaly_explanations': ['Analyse LLM non disponible'],
            'correlations_found': [],
            'is_critical': False
        }
        
        summary = self.detector.generate_llm_summary(minimal_analysis, self.metrics)
        
        # Devrait retourner un message par défaut
        self.assertIn('Aucune anomalie significative', summary)
    
    @patch.object(LLMAnomalyDetector, 'detect_anomalies')
    def test_analyze_metrics_success(self, mock_detect):
        """Test analyse réussie des métriques."""
        mock_llm_analysis = {
            'anomalies_detected': {
                'cpu': True,
                'memory': False,
                'latency': True,
                'disk': False,
                'io': False,
                'error_rate': False,
                'temperature': False,
                'power': False,
                'services': True
            },
            'severity_score': 6,
            'is_critical': False,
            'risk_assessment': 'Charge modérée avec services dégradés',
            'ai_confidence': 0.8
        }
        mock_detect.return_value = mock_llm_analysis
        
        result = self.detector.analyze_metrics(self.metrics)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, AnomalyDetection)
        
        # Vérifier les anomalies détectées
        self.assertTrue(result.cpu_anomaly)
        self.assertFalse(result.memory_anomaly)
        self.assertTrue(result.latency_anomaly)
        self.assertTrue(result.service_anomaly)
        
        # Vérifier les métadonnées
        self.assertEqual(result.severity_score, 6)
        self.assertFalse(result.is_critical)
        self.assertEqual(result.analysis_method, 'llm')
        
        # Vérifier que les métriques sont mises à jour
        self.metrics.refresh_from_db()
        self.assertTrue(self.metrics.analysis_completed)
        self.assertTrue(self.metrics.is_anomalous)  # Car il y a des anomalies détectées
    
    @patch.object(LLMAnalysisEngine, 'is_available', False)
    def test_analyze_metrics_llm_unavailable(self):
        """Test analyse quand LLM indisponible."""
        result = self.detector.analyze_metrics(self.metrics)
        
        self.assertIsNone(result)
        
        # Vérifier que les métriques ne sont pas modifiées
        self.metrics.refresh_from_db()
        self.assertFalse(self.metrics.analysis_completed)
        self.assertFalse(self.metrics.is_anomalous)
    
    def test_batch_analysis(self):
        """Test analyse en lot."""
        # Créer quelques métriques supplémentaires
        InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=45.0,
            memory_usage=50.0,
            latency_ms=150,
            disk_usage=40.0,
            network_in_kbps=800,
            network_out_kbps=600,
            io_wait=2.0,
            thread_count=60,
            active_connections=15,
            error_rate=0.005,
            uptime_seconds=172800,
            temperature_celsius=45.0,
            power_consumption_watts=180,
            service_status={'api': 'online', 'db': 'online'}
        )
        
        metrics_queryset = InfrastructureMetrics.objects.all()
        
        with patch.object(self.detector, 'analyze_metrics') as mock_analyze:
            # Simuler succès pour toutes les métriques
            mock_analyze.return_value = AnomalyDetection(
                severity_score=5,
                analysis_method='llm'
            )
            mock_analyze.return_value.anomaly_summary = 'LLM: Test analysis'
            
            results = self.detector.analyze_batch_metrics(metrics_queryset)
            
            self.assertEqual(results['total'], 2)
            self.assertEqual(results['analyzed'], 2)
            self.assertEqual(results['errors'], 0)
            self.assertEqual(results['llm_available'], 2)


class TestAnomalyAnalysisPrompts(TestCase):
    """Tests pour les prompts d'analyse d'anomalies."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.prompts = AnomalyAnalysisPrompts()
        
        self.sample_metrics = {
            'timestamp': '2023-10-01T12:00:00Z',
            'cpu_usage': 85.0,
            'memory_usage': 75.0,
            'latency_ms': 300,
            'disk_usage': 70.0,
            'error_rate': 0.05,
            'temperature_celsius': 65.0
        }
    
    def test_anomaly_detection_prompt(self):
        """Test génération du prompt de détection d'anomalies."""
        prompt = self.prompts.get_anomaly_detection_prompt(self.sample_metrics)
        
        # Vérifier la présence d'éléments clés
        self.assertIn('expert en infrastructure IT', prompt)
        self.assertIn('anomalies', prompt)
        self.assertIn('JSON', prompt)
        self.assertIn('cpu_usage', prompt)
        self.assertIn('memory_usage', prompt)
        
        # Vérifier que les métriques sont incluses
        self.assertIn('85.0', prompt)  # cpu_usage
        self.assertIn('75.0', prompt)  # memory_usage
        self.assertIn('300', prompt)   # latency_ms
        
        # Vérifier la structure JSON attendue
        self.assertIn('anomalies_detected', prompt)
        self.assertIn('severity_score', prompt)
        self.assertIn('ai_confidence', prompt)
    
    def test_severity_assessment_prompt(self):
        """Test génération du prompt d'évaluation de sévérité."""
        prompt = self.prompts.get_severity_assessment_prompt(self.sample_metrics)
        
        # Vérifier la présence d'éléments clés
        self.assertIn('sévérité', prompt)
        self.assertIn('Impact immédiat', prompt)
        self.assertIn('effet domino', prompt)
        self.assertIn('services affectés', prompt)
        
        # Vérifier les critères d'évaluation
        self.assertIn('0-3 points', prompt)
        self.assertIn('0-2 points', prompt)
        
        # Vérifier la structure de réponse
        self.assertIn('severity_score', prompt)
        self.assertIn('immediate_risk', prompt)
        self.assertIn('business_impact', prompt)
    
    def test_correlation_analysis_prompt(self):
        """Test génération du prompt d'analyse de corrélations."""
        prompt = self.prompts.get_correlation_analysis_prompt(self.sample_metrics)
        
        # Vérifier la présence d'éléments clés
        self.assertIn('corrélations', prompt)
        self.assertIn('patterns', prompt)
        self.assertIn('Relations causales', prompt)
        
        # Vérifier la structure de réponse
        self.assertIn('strong_correlations', prompt)
        self.assertIn('anomalous_patterns', prompt)
        self.assertIn('missing_correlations', prompt)
        self.assertIn('insights', prompt)
    
    def test_fallback_response(self):
        """Test réponse de fallback."""
        # Test avec score par défaut
        fallback = self.prompts.get_fallback_response()
        
        self.assertIsInstance(fallback, dict)
        self.assertEqual(fallback['severity_score'], 5)
        self.assertEqual(fallback['ai_confidence'], 0.0)
        self.assertFalse(fallback['is_critical'])
        
        # Vérifier toutes les anomalies à False
        anomalies = fallback['anomalies_detected']
        for detected in anomalies.values():
            self.assertFalse(detected)
        
        # Vérifier les messages par défaut
        self.assertEqual(fallback['anomaly_explanations'], ['Analyse LLM non disponible'])
        self.assertEqual(fallback['correlations_found'], [])
        self.assertEqual(fallback['recommended_actions'], ['Utiliser analyse classique par seuils'])
        
        # Test avec score personnalisé
        custom_fallback = self.prompts.get_fallback_response(severity_score=8)
        self.assertEqual(custom_fallback['severity_score'], 8)


class TestAnomalyDetectionService(TestCase):
    """Tests pour le service principal de détection d'anomalies."""
    
    def setUp(self):
        """Configuration des données de test."""
        self.metrics = InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=75.0,
            memory_usage=65.0,
            latency_ms=200,
            disk_usage=45.0,
            network_in_kbps=1000,
            network_out_kbps=800,
            io_wait=3.0,
            thread_count=80,
            active_connections=25,
            error_rate=0.01,
            uptime_seconds=86400,
            temperature_celsius=50.0,
            power_consumption_watts=220,
            service_status={'api': 'online', 'db': 'online'}
        )
    
    def test_service_initialization_classic(self):
        """Test initialisation avec méthode classique."""
        service = AnomalyDetectionService(method='classic')
        
        self.assertEqual(service.method, 'classic')
        self.assertIsInstance(service.detector, ClassicAnomalyDetector)
        # Le service classique est toujours disponible
        self.assertTrue(hasattr(service, 'detector'))
    
    def test_service_initialization_llm(self):
        """Test initialisation avec méthode LLM."""
        service = AnomalyDetectionService(method='llm')
        
        self.assertEqual(service.method, 'llm')
        self.assertIsInstance(service.detector, LLMAnomalyDetector)
    
    def test_service_initialization_invalid_method(self):
        """Test initialisation avec méthode invalide."""
        # Le service utilise 'classic' par défaut pour les méthodes invalides
        service = AnomalyDetectionService(method='invalid_method')
        self.assertEqual(service.method, 'classic')
    
    def test_analyze_metrics_classic(self):
        """Test analyse avec méthode classique."""
        service = AnomalyDetectionService(method='classic')
        
        result = service.analyze_metrics(self.metrics)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, AnomalyDetection)
        self.assertEqual(result.analysis_method, 'classic')
    
    def test_get_method_info(self):
        """Test récupération des informations de méthode."""
        # Méthode classique
        classic_service = AnomalyDetectionService(method='classic')
        classic_info = classic_service.get_method_info()
        
        self.assertIsInstance(classic_info, dict)
        # Test que les informations basiques sont présentes
        self.assertIn('current_method', classic_info)
        self.assertEqual(classic_info['current_method'], 'classic')
        
        # Méthode LLM
        llm_service = AnomalyDetectionService(method='llm')
        llm_info = llm_service.get_method_info()
        
        self.assertIsInstance(llm_info, dict)
        self.assertIn('current_method', llm_info)
        self.assertEqual(llm_info['current_method'], 'llm')
    
    def test_batch_analysis(self):
        """Test analyse en lot."""
        # Créer quelques métriques supplémentaires
        InfrastructureMetrics.objects.create(
            timestamp=timezone.now(),
            cpu_usage=45.0,
            memory_usage=50.0,
            latency_ms=120,
            disk_usage=40.0,
            network_in_kbps=800,
            network_out_kbps=600,
            io_wait=2.0,
            thread_count=60,
            active_connections=15,
            error_rate=0.005,
            uptime_seconds=172800,
            temperature_celsius=45.0,
            power_consumption_watts=180,
            service_status={'api': 'online', 'db': 'online'}
        )
        
        service = AnomalyDetectionService(method='classic')
        metrics_queryset = InfrastructureMetrics.objects.all()
        
        results = service.analyze_batch_metrics(metrics_queryset)
        
        self.assertIsInstance(results, dict)
        self.assertEqual(results['total'], 2)
        self.assertIn('analyzed', results)
        self.assertIn('errors', results)
