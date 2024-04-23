BUILDER_STABLE_V := $(shell jq -r '.BUILDER_STABLE_V' < .versions.json) 
PREPARER_STABLE_V := $(shell jq -r '.PREPARER_STABLE_V' < .versions.json) 
# DOCKER_REGISTRY = '<INSERT_AWS_ACCOUNT_NUMBER>.dkr.ecr.<INSERT_AWS_REGION>.amazonaws.com'
DOCKER_REGISTRY = c2dhunilu


login:
	docker login --username c2dhadmin

preparer/build:
	docker build -t dgtmon-dev-preparer src/preparer

preparer/tag:
	docker tag dgtmon-dev-preparer ${DOCKER_REGISTRY}/dgtmon-dev-preparer:${PREPARER_STABLE_V}

preparer/push:
	docker push ${DOCKER_REGISTRY}/dgtmon-dev-preparer:${PREPARER_STABLE_V}

builder/build:
	docker build -t dgtmon-dev-builder src/builder

builder/tag:
	docker tag dgtmon-dev-builder ${DOCKER_REGISTRY}/dgtmon-dev-builder:${BUILDER_STABLE_V}

builder/push:
	docker push ${DOCKER_REGISTRY}/dgtmon-dev-builder:${BUILDER_STABLE_V}
