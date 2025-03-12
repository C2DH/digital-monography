ENTRYPOINT_STABLE_V := $(shell jq -r '.ENTRYPOINT_STABLE_V' < .versions.json) 
DROPBOX_STABLE_V := $(shell jq -r '.DROPBOX_STABLE_V' < .versions.json) 
BUILDER_STABLE_V := $(shell jq -r '.BUILDER_STABLE_V' < .versions.json) 
PREPARER_STABLE_V := $(shell jq -r '.PREPARER_STABLE_V' < .versions.json) 
GITHUB_STABLE_V  := $(shell jq -r '.GITHUB_STABLE_V' < .versions.json) 
VERIFIER_STABLE_V  := $(shell jq -r '.VERIFIER_STABLE_V' < .versions.json) 
GPU_STABLE_V  := $(shell jq -r '.GPU_STABLE_V' < .versions.json) 
WORDPROCESSOR_STABLE_V  := $(shell jq -r '.WORDPROCESSOR_STABLE_V' < .versions.json) 
LOCAL_STABLE_V := $(shell jq -r '.LOCAL_STABLE_V' < .versions.json)
AWS_KMS_ARN = 'arn:aws:kms:eu-west-1:367031255351:key/34644061-6a4d-4414-b0e4-90a9df0e2cff'
DOCKER_ECR = 367031255351.dkr.ecr.eu-west-1.amazonaws.com
DOCKER_HUB = c2dhunilu


test/prep:
	cp '/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books-Testing/links/01_a.docx' tests/_fixtures/refs/01_a.docx
	cp '/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books-Testing/links/02_b.docx' tests/_fixtures/refs/02_b.docx
	cp -R '/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books-Testing/book-content-examples/' tests/_fixtures/

test/run:
	DGTMON_DEBUG=1 python -m pytest tests/preparer/ tests/verifier/ tests/builder/

test:
	DGTMON_DEBUG=1 python -m pytest tests/preparer/ tests/verifier/ tests/builder/

login:
	aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ${DOCKER_ECR}
	docker login --username c2dhadmin

dev/build:
	docker compose build --no-cache

dev/tag:
	docker tag dgtmon-dev-local ${DOCKER_HUB}/dgtmon-dev-local:${LOCAL_STABLE_V}
	docker tag dgtmon-dev-local ${DOCKER_HUB}/dgtmon-dev-local:latest

dev/push:
	docker push ${DOCKER_HUB}/dgtmon-dev-local:${LOCAL_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-local:latest

dev/start:
	docker compose up --detach

dev/test:
	docker compose run main make test

dev/draft:
	docker compose run main python scripts/prepare_and_build.py book_path=data/input/$(SLUG)

copy/audit:
	cp src/_common/audit.py src/dropbox/audit.py
	cp src/_common/audit.py src/preparer/audit.py
	cp src/_common/audit.py src/builder/audit.py
	cp src/_common/audit.py src/github/audit.py
	cp src/_common/audit.py src/verifier/audit.py

copy/constants:
	cp src/_common/constants.py scripts/constants.py
	cp src/_common/constants.py src/entrypoint/constants.py
	cp src/_common/constants.py src/dropbox/constants.py
	cp src/_common/constants.py src/preparer/constants.py
	cp src/_common/constants.py src/builder/constants.py
	cp src/_common/constants.py src/github/constants.py
	cp src/_common/constants.py src/verifier/constants.py
	cp src/_common/constants.py src/gpu/constants.py
	cp src/_common/constants.py src/wordprocessor/constants.py

copy/keys:
	cp src/_common/keys.py src/dropbox/keys.py
	cp src/_common/keys.py src/preparer/keys.py
	cp src/_common/keys.py src/builder/keys.py
	cp src/_common/keys.py src/github/keys.py
	cp src/_common/keys.py src/verifier/keys.py
	cp src/_common/keys.py src/wordprocessor/keys.py

copy/metadata:
	cp src/_common/metadata.py src/preparer/metadata.py
	cp src/_common/metadata.py src/builder/metadata.py
	cp src/_common/metadata.py src/verifier/metadata.py
	cp src/_common/metadata.py src/wordprocessor/metadata.py

copy/html2md:
	cp src/_common/html2md.py src/preparer/html2md.py
	cp src/_common/html2md.py src/verifier/html2md.py
	cp src/_common/html2md.py src/builder/html2md.py

copy/models:
	cp src/_common/models/assets_base.py src/preparer/models/assets_base.py

entrypoint/build:
	cp src/_common/constants.py src/entrypoint/constants.py
	docker build -t dgtmon-dev-entrypoint src/entrypoint

entrypoint/tag:
	docker tag dgtmon-dev-entrypoint ${DOCKER_ECR}/dgtmon-dev-entrypoint:${ENTRYPOINT_STABLE_V}
	docker tag dgtmon-dev-entrypoint ${DOCKER_HUB}/dgtmon-dev-entrypoint:${ENTRYPOINT_STABLE_V}

entrypoint/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-entrypoint:${ENTRYPOINT_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-entrypoint:${ENTRYPOINT_STABLE_V}

entrypoint/make: entrypoint/build entrypoint/tag entrypoint/push

dropbox/build:
	cp src/_common/constants.py src/dropbox/constants.py
	cp src/_common/keys.py src/dropbox/keys.py
	docker build -t dgtmon-dev-dropbox src/dropbox

dropbox/tag:
	docker tag dgtmon-dev-dropbox ${DOCKER_ECR}/dgtmon-dev-dropbox:${DROPBOX_STABLE_V}
	docker tag dgtmon-dev-dropbox ${DOCKER_HUB}/dgtmon-dev-dropbox:${DROPBOX_STABLE_V}

dropbox/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-dropbox:${DROPBOX_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-dropbox:${DROPBOX_STABLE_V}

dropbox/make: dropbox/build dropbox/tag dropbox/push

preparer/build:
	cp src/_common/constants.py src/preparer/constants.py
	cp src/_common/keys.py src/preparer/keys.py
	cp src/_common/metadata.py src/preparer/metadata.py
	cp src/_common/html2md.py src/preparer/html2md.py
	docker build -t dgtmon-dev-preparer src/preparer

preparer/tag:
	docker tag dgtmon-dev-preparer ${DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker tag dgtmon-dev-preparer ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_STABLE_V}

preparer/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_STABLE_V}

preparer/make: preparer/build preparer/tag preparer/push

builder/build:
	cp src/_common/constants.py src/builder/constants.py
	cp src/_common/keys.py src/builder/keys.py
	cp src/_common/metadata.py src/builder/metadata.py
	docker build -t dgtmon-dev-builder src/builder

builder/tag:
	docker tag dgtmon-dev-builder ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker tag dgtmon-dev-builder ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

builder/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_STABLE_V}

builder/make: builder/build builder/tag builder/push

github/build:
	cp src/_common/constants.py src/github/constants.py
	cp src/_common/keys.py src/github/keys.py
	docker build -t dgtmon-dev-github src/github

github/tag:
	docker tag dgtmon-dev-github ${DOCKER_ECR}/dgtmon-dev-github:${GITHUB_STABLE_V}
	docker tag dgtmon-dev-github ${DOCKER_HUB}/dgtmon-dev-github:${GITHUB_STABLE_V}

github/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-github:${GITHUB_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-github:${GITHUB_STABLE_V}

github/make: github/build github/tag github/push

verifier/build:
	cp src/_common/constants.py src/verifier/constants.py
	cp src/_common/keys.py src/verifier/keys.py
	cp src/_common/metadata.py src/verifier/metadata.py
	cp src/_common/html2md.py src/verifier/html2md.py
	docker build -t dgtmon-dev-verifier src/verifier

verifier/tag:
	docker tag dgtmon-dev-verifier ${DOCKER_ECR}/dgtmon-dev-verifier:${VERIFIER_STABLE_V}
	docker tag dgtmon-dev-verifier ${DOCKER_HUB}/dgtmon-dev-verifier:${VERIFIER_STABLE_V}

verifier/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-verifier:${VERIFIER_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-verifier:${VERIFIER_STABLE_V}

verifier/make: verifier/build verifier/tag verifier/push

gpu/build:
	cp src/_common/constants.py src/gpu/constants.py
	docker build -t dgtmon-dev-gpu src/gpu

gpu/tag:
	docker tag dgtmon-dev-gpu ${DOCKER_ECR}/dgtmon-dev-gpu:${GPU_STABLE_V}
	docker tag dgtmon-dev-gpu ${DOCKER_HUB}/dgtmon-dev-gpu:${GPU_STABLE_V}

gpu/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-gpu:${GPU_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-gpu:${GPU_STABLE_V}

gpu/make: gpu/build gpu/tag gpu/push

wordprocessor/build:
	cp src/_common/constants.py src/wordprocessor/constants.py
	docker build -t dgtmon-dev-wordprocessor src/wordprocessor

wordprocessor/tag:
	docker tag dgtmon-dev-wordprocessor ${DOCKER_ECR}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_STABLE_V}
	docker tag dgtmon-dev-wordprocessor ${DOCKER_HUB}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_STABLE_V}

wordprocessor/push:
	docker push ${DOCKER_ECR}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_STABLE_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_STABLE_V}

wordprocessor/make: wordprocessor/build wordprocessor/tag wordprocessor/push

