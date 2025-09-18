.PHONY: install run migrate test clean shell

# Installation des dépendances
install:
	poetry install

# Démarrage du serveur de développement
run:
	poetry run python manage.py runserver

# Migrations de la base de données
migrate:
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate

# Exécution des tests
test:
	poetry run python manage.py test

# Nettoyage des fichiers temporaires
clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name ".pytest_cache" -type d -exec rm -rf {} +

# Shell Django
shell:
	poetry run python manage.py shell

# Collecte des fichiers statiques
collectstatic:
	poetry run python manage.py collectstatic --noinput

# Commande complète de setup
setup: install migrate
	@echo "Projet configuré avec succès!"

# Démarrage rapide
start: setup run

# Aide
help:
	@echo "Commandes disponibles:"
	@echo "  make install      - Installer les dépendances"
	@echo "  make run          - Démarrer le serveur"
	@echo "  make migrate      - Exécuter les migrations"
	@echo "  make test         - Lancer les tests"
	@echo "  make shell        - Ouvrir le shell Django"
	@echo "  make setup        - Installation + migrations"
	@echo "  make start        - Setup complet + démarrage"
	@echo "  make clean        - Nettoyer les fichiers temporaires"