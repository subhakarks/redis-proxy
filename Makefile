VERSION := "latest"
PACKAGE := "redis_proxy"
DOCKER_BUILD_OPTS := --tag
DOCKER_IMAGE := ${PACKAGE}:${VERSION}
DOCKER_COMPOSE_DOWN_OPTS := --volumes
DOCKER_COMPOSE_UP_OPTS := --detach --remove-orphans
DOCKER_RUN_OPTS := -d -p 8956:8956 --name "redis-proxy-instance"

build:
	docker image build ${DOCKER_BUILD_OPTS} $(DOCKER_IMAGE) .

start: build
	docker-compose up ${DOCKER_COMPOSE_UP_OPTS}

stop:
	docker-compose down ${DOCKER_COMPOSE_DOWN_OPTS}

run: build
	docker run ${DOCKER_RUN_OPTS} $(DOCKER_IMAGE)

build-test:
	docker image build --tag "redis-proxy_system_tests:latest" system_tests

test: build-test
	docker-compose up --build --remove-orphans system_tests

test2: build build-test
	docker-compose -f docker-compose-tests.yml up --detach --remove-orphans --scale system_tests=0
	docker-compose -f docker-compose-tests.yml up --remove-orphans system_tests
