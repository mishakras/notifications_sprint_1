DOCKER_COMPOSE_FILES ?= $(shell find . -maxdepth 1 -type f -name "*.yml" -exec printf -- '-f %s ' {} +; echo)

## ▸▸▸ Docker commands ◂◂◂
.PHONY: config
config:			## Show Docker config
	docker compose ${DOCKER_COMPOSE_FILES} config

.PHONY: up
up:			## Run Docker services
	docker compose ${DOCKER_COMPOSE_FILES} up --detach

.PHONY: down
down:			## Stop Docker services
	docker compose ${DOCKER_COMPOSE_FILES} down

.PHONY: ps
ps:			## Show Docker containers info
	docker ps --size --all --filter "name=theatre*"

freeze:
	pip freeze > requirements.txt

full-install: install, test-install

install:
	pip install -r requirements.txt

test-install:
	pip install -r test-requirements.txt

lint: flake black isort

flake:
	flake8 .

black:
	black --color --check --diff .

isort:
	isort . --check --diff

## ▸▸▸ Docker commands for Test◂◂◂
TEST_DOCKER_COMPOSE_FILES ?= $(shell find tests -maxdepth 2 -type f -name "*.yml" -exec printf -- '-f %s ' {} +; echo)

test-config:			## Show Docker config
	docker compose ${TEST_DOCKER_COMPOSE_FILES} config

test-up:			## Run Docker services
	docker compose ${TEST_DOCKER_COMPOSE_FILES} up --detach

test-down:			## Stop Docker services
	docker compose ${TEST_DOCKER_COMPOSE_FILES} down

superuser:			## Create SuperUser
	docker compose exec fastapi-service python fastapi_solution/src/cli/admin.py
