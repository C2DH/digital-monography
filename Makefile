BUILDER_STABLE_V := $(shell jq -r '.BUILDER_STABLE_V' < .versions.json) 
PREPARER_STABLE_V := $(shell jq -r '.PREPARER_STABLE_V' < .versions.json) 
DOCKER_ECR = 367031255351.dkr.ecr.eu-west-1.amazonaws.com
DOCKER_HUB = c2dhunilu


login:
	docker login --username c2dhadmin

preparer/build:
	docker build -t dgtmon-dev-preparer src/preparer
	docker build -t dgtmon-dev-preparer src/preparer

preparer/tag:
	docker tag dgtmon-dev-preparer ${DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker tag dgtmon-dev-preparer ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_STABLE_V}

preparer/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_STABLE_V}

builder/build:
	docker build -t dgtmon-dev-builder src/builder
	docker build -t dgtmon-dev-builder src/builder

builder/tag:
	docker tag dgtmon-dev-builder ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker tag dgtmon-dev-builder ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

builder/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}
