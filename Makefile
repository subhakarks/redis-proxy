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
