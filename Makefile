.PHONY: help dev test lint deploy simulate loadtest clean build-all docker-up docker-down

help:
	@echo "FoodBridge Cloud-Native Platform Commands:"
	@echo "  make dev        - Start local microservices and frontend"
	@echo "  make test       - Run all pytest unit tests and frontend tests"
	@echo "  make lint       - Run ruff/flake8 and typescript typechecks"
	@echo "  make deploy     - Run Terraform deployment script"
	@echo "  make simulate   - Run the real-time rush scenario simulator"
	@echo "  make loadtest   - Run Locust load testing suite"
	@echo "  make docker-up  - Launch all services with docker-compose"
	@echo "  make docker-down- Stop all docker-compose services"

dev:
	docker compose up --build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

test:
	python scripts/test_runner.py

lint:
	python -m flake8 services/ --max-line-length=120 --exclude=venv,.venv,__pycache__
	cd web && npm run lint || true

deploy:
	bash scripts/deploy.sh

simulate:
	python simulator/simulate.py --scenario scenarios/wedding_rush.json --speed 5

loadtest:
	locust -f simulator/load_test/locustfile.py --headless -u 20 -r 5 --run-time 1m --host http://localhost:8001

build-all:
	docker compose build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
