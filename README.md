# Infrastructure Optimizer - Solution d'Optimisation d'Infrastructure Technique

## Description

**Infrastructure Optimizer** est une solution complete d'analyse et d'optimisation d'infrastructure technique developpee pour Devoteam. Cette application Django permet d'ingerer des metriques systeme, de detecter automatiquement les anomalies et de generer des recommandations d'optimisation intelligentes.

## Fonctionnalites Principales

### Workflow Complet d'Optimisation
1. **Ingestion de Donnees** - Import de metriques d'infrastructure (JSON)
2. **Analyse d'Anomalies** - Detection automatique via methodes classiques ou IA
3. **Generation de Recommandations** - Suggestions d'optimisation contextuelles

### Capacites Metier
- **Detection d'anomalies multi-metrique** (CPU, memoire, latence, disque, I/O, etc.)
- **Analyse intelligente via Azure OpenAI** pour des insights approfondis
- **Recommandations actionables** avec priorites et delais d'implementation
- **Interface web moderne** avec workflow guide et historique complet
- **API REST complete** avec documentation Swagger integree

## Architecture Technique

### Framework & Technologies
- **Backend** : Django 5.2.6 + Django REST Framework 3.16.1
- **Base de donnees** : SQLite (developpement) - extensible PostgreSQL/MySQL
- **IA/ML** : Azure OpenAI API (GPT-4), scikit-learn, numpy, pandas
- **Frontend** : HTML5/CSS3/JavaScript vanilla avec design responsive
- **Documentation API** : drf-yasg (Swagger/OpenAPI)
- **Gestionnaire de dependances** : Poetry

### Structure Modulaire

```
devoteam_infrastructure_optimizer/
├── infrastructure_optimization/
│   └── core/
│       └── services/
├── ingestion/
│   ├── migrations/
│   └── services/
├── analysis/
│   ├── migrations/
│   └── services/
│       ├── classic/
│       └── llm/
├── recommendations/
│   ├── migrations/
│   └── services/
│       ├── classic/
│       └── llm/
├── frontend/
├── templates/
│   └── frontend/
└── sample_data/
```

## Modeles de Donnees

### InfrastructureMetrics
Stockage des metriques d'infrastructure avec 15+ indicateurs :
- **Performance** : CPU, memoire, latence, disque
- **Reseau** : Trafic entrant/sortant (Kbps)
- **Avancees** : I/O wait, threads, connexions, taux d'erreur
- **Materiel** : Temperature, consommation electrique, uptime
- **Services** : Statuts des composants (database, api_gateway, cache)

### AnomalyDetection
Resultats d'analyse avec :
- Detection granulaire par type de metrique
- Score de severite (0-10)
- Resume textuel des anomalies
- Methode d'analyse utilisee (classic/llm)

### RecommendationReport
Rapports de recommandations incluant :
- Resume executif et analyse detaillee
- Recommandations structurees avec priorites
- Impact estime et delais d'implementation
- Methode de generation (classic/llm)

## API REST Endpoints

### Ingestion (`/api/ingestion/`)
- `POST /ingest` - Ingestion metrique unique
- `POST /bulk_ingestion` - Ingestion par lot
- `GET /metrics` - Liste des metriques ingerees

### Analyse (`/api/analysis/`)
- `POST /analyze` - Lancement analyse d'anomalies
- `GET /anomalies` - Liste des analyses effectuees
- `GET /result/{id}` - Details d'une analyse

### Recommandations (`/api/recommendations/`)
- `POST /generate` - Generation de recommandations
- `GET /reports` - Liste des rapports
- `GET /reports/{id}` - Details d'un rapport

### Documentation
- `/swagger/` - Interface Swagger interactive
- `/redoc/` - Documentation ReDoc

## Moteurs d'Intelligence Artificielle

### Analyse d'Anomalies
1. **Methode Classique** : Detection par seuils configurables
2. **Methode LLM** : Analyse contextuelle via Azure OpenAI avec prompts specialises

### Generation de Recommandations
1. **Methode Classique** : Regles metier predefinies
2. **Methode LLM** : Recommandations intelligentes contextuelles avec :
   - Analyse des causes racines
   - Suggestions d'optimisation specifiques
   - Planification d'implementation

## Interface Utilisateur

### Dashboard Moderne
- **Workflow guide en 3 etapes** avec indicateurs visuels de progression
- **Ingestion flexible** : saisie JSON directe ou import de fichier
- **Selection de methodes** : choix entre approches classiques et IA
- **Historique complet** avec filtres par type (metriques, analyses, recommandations)
- **Modals detaillees** pour visualisation approfondie des resultats

### Fonctionnalites UX
- Design responsive avec variables CSS personnalisees
- Animations et transitions fluides
- Systeme d'alertes contextuelles
- Navigation intuitive avec etats visuels clairs

## Installation et Configuration

### Prerequis
- Python 3.10+
- Poetry (gestionnaire de dependances)

### Installation
```bash
# Cloner le projet
git clone <repository-url>
cd devoteam_infrastructure_optimizer

# Installer les dependances
make install
# ou poetry install

# Configurer la base de donnees
make migrate
# ou poetry run python manage.py migrate

# Demarrer le serveur
make run
# ou poetry run python manage.py runserver
```

### Configuration Azure OpenAI (Optionnelle)
Creer un fichier `.env` :
```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01
```

### Commandes Make Disponibles
```bash
make install      # Installation des dependances
make run          # Demarrage du serveur
make migrate      # Execution des migrations
make test         # Lancement des tests
make shell        # Shell Django
make setup        # Installation + migrations
make start        # Setup complet + demarrage
make clean        # Nettoyage des fichiers temporaires
make help         # Aide sur les commandes
```

## Seuils de Detection d'Anomalies

Configuration par defaut dans `settings.py` :
```python
ANOMALY_THRESHOLDS = {
    'cpu_usage': 80,              # CPU > 80%
    'memory_usage': 85,           # Memoire > 85%
    'latency_ms': 500,           # Latence > 500ms
    'disk_usage': 90,            # Disque > 90%
    'io_wait': 20,               # I/O wait > 20%
    'error_rate': 0.05,          # Taux d'erreur > 5%
    'temperature_celsius': 75,    # Temperature > 75°C
    'power_consumption_watts': 400 # Consommation > 400W
}
```

## Format des Donnees d'Entree

### Metrique Unique
```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "cpu_usage": 85,
  "memory_usage": 70,
  "latency_ms": 250,
  "disk_usage": 65,
  "network_in_kbps": 1200,
  "network_out_kbps": 900,
  "io_wait": 5,
  "thread_count": 150,
  "active_connections": 45,
  "error_rate": 0.02,
  "uptime_seconds": 360000,
  "temperature_celsius": 65,
  "power_consumption_watts": 250,
  "service_status": {
    "database": "online",
    "api_gateway": "degraded",
    "cache": "online"
  }
}
```

### Ingestion par Lot
```json
[
  { /* metrique 1 */ },
  { /* metrique 2 */ },
  { /* metrique N */ }
]
```

## Exemples d'Utilisation

### 1. Workflow Complet via Interface Web
1. Acceder a `http://localhost:8000`
2. **Etape 1** : Coller les donnees JSON ou importer un fichier
3. **Etape 2** : Choisir la methode d'analyse (Classic/LLM) et lancer
4. **Etape 3** : Selectionner la methode de recommandations et generer
5. Consulter l'historique et les details des rapports

### 2. Utilisation API Directe
```bash
# Ingestion d'une metrique
curl -X POST http://localhost:8000/api/ingestion/ingest \
  -H "Content-Type: application/json" \
  -d @sample_data/single_metric.json

# Analyse d'anomalies
curl -X POST "http://localhost:8000/api/analysis/analyze?metrics_id=1&method=llm"

# Generation de recommandations
curl -X POST "http://localhost:8000/api/recommendations/generate?metrics_id=1&method=llm"
```

## Tests et Validation

- Donnees d'exemple dans `sample_data/`

### Lancement des Tests
```bash
make test
# ou poetry run python manage.py test
```
---

**Version** : 0.1.0  
**Date de creation** : 2025 
**Derniere mise a jour** : 2025 
**Auteur** : Candidat Devoteam  
**Framework** : Django 5.2.6  
**Python** : 3.10+