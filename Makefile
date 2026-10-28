.PHONY: help install test run-web run-tui run-watcher seed verify-isolation clean docker-build docker-up

PYTHON ?= python3
PIP ?= pip

help:
	@echo "SovereignLedger Operations Manual:"
	@echo "  make install            - Install local dependencies"
	@echo "  make seed               - Generate test bank CSVs and simulated invoices"
	@echo "  make run-web            - Launch judges' interactive live web dashboard"
	@echo "  make run-tui            - Launch Textual terminal dashboard"
	@echo "  make run-watcher        - Start dropzone inotify daemon"
	@echo "  make test               - Execute full automated test suite"
	@echo "  make verify-isolation   - Audit network sandbox & zero-egress kernel boundary"
	@echo "  make docker-build       - Compile production OpenShell container"
	@echo "  make docker-up          - Spin up SovereignLedger stack in containerized isolation"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

seed:
	$(PYTHON) scripts/seed_data.py

run-web:
	$(PYTHON) -m src.cli serve-web --host 0.0.0.0 --port 8080

run-tui:
	$(PYTHON) -m src.cli tui

run-watcher:
	$(PYTHON) -m src.cli ingest

test:
	pytest tests/ -v -s

verify-isolation:
	bash scripts/verify_network_isolation.sh

clean:
	rm -rf data/incoming/* db/* skills/parsers/aws*.py build/ dist/ *.egg-info .pytest_cache
	mkdir -p data/incoming db skills/parsers

docker-build:
	docker compose build

docker-up:
	docker compose up
