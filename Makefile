BUILDER_STABLE_V := $(shell jq -r '.BUILDER_STABLE_V' < .versions.json) 
PREPARER_STABLE_V := $(shell jq -r '.PREPARER_STABLE_V' < .versions.json) 
AWS_KMS_ARN = 'arn:aws:kms:eu-west-1:367031255351:key/34644061-6a4d-4414-b0e4-90a9df0e2cff'
DOCKER_ECR = 367031255351.dkr.ecr.eu-west-1.amazonaws.com
DOCKER_HUB = c2dhunilu


login:
	aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ${DOCKER_ECR}
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

builder/tag:
	docker tag dgtmon-dev-builder ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker tag dgtmon-dev-builder ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

builder/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

all/build:
	docker build -t dgtmon-dev-preparer src/preparer
	docker build -t dgtmon-dev-builder src/builder

all/tag:
	docker tag dgtmon-dev-preparer ${DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker tag dgtmon-dev-preparer ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker tag dgtmon-dev-builder ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker tag dgtmon-dev-builder ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

all/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker push ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

encrypt:
	sops --kms ${AWS_KMS_ARN} -e $(file) > $(file)
