VERSION := "latest"
PROXY_PACKAGE := "redis_proxy"
SYSTEM_TESTS := "system_tests"
PROXY_TESTS_PACKAGE := "redis_proxy_system_tests"

DOCKER_BUILD_OPTS := --tag
DOCKER_COMPOSE_DOWN_OPTS := --volumes
DOCKER_COMPOSE_UP_OPTS := --detach --remove-orphans
DOCKER_PROXY_IMAGE := ${PROXY_PACKAGE}:${VERSION}
DOCKER_PROXY_TESTS_IMAGE := ${PROXY_TESTS_PACKAGE}:${VERSION}

build:
	docker image build ${DOCKER_BUILD_OPTS} $(DOCKER_PROXY_IMAGE) .

start: build
	docker-compose up ${DOCKER_COMPOSE_UP_OPTS}

stop:
	docker-compose down ${DOCKER_COMPOSE_DOWN_OPTS}

build-test:
	docker image build ${DOCKER_BUILD_OPTS} ${DOCKER_PROXY_TESTS_IMAGE} ${SYSTEM_TESTS}

test: build build-test
	docker-compose -f docker-compose-tests.yml up ${DOCKER_COMPOSE_UP_OPTS} --scale ${SYSTEM_TESTS}=0
	docker-compose -f docker-compose-tests.yml up ${SYSTEM_TESTS}

test-stop:
	docker-compose -f docker-compose-tests.yml down ${DOCKER_COMPOSE_DOWN_OPTS}
