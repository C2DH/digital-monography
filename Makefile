ENTRYPOINT_LATEST_V := $(shell jq -r '.ENTRYPOINT.LATEST' < .versions.json)
DROPBOX_LATEST_V := $(shell jq -r '.DROPBOX.LATEST' < .versions.json)
BUILDER_LATEST_V := $(shell jq -r '.BUILDER.LATEST' < .versions.json)
BUILDERv2_LATEST_V := $(shell jq -r '.BUILDERv2.LATEST' < .versions.json)
PREPARER_LATEST_V := $(shell jq -r '.PREPARER.LATEST' < .versions.json)
GITHUB_LATEST_V  := $(shell jq -r '.GITHUB.LATEST' < .versions.json)
VERIFIER_LATEST_V  := $(shell jq -r '.VERIFIER.LATEST' < .versions.json)
GPU_LATEST_V  := $(shell jq -r '.GPU.LATEST' < .versions.json)
ORM_LATEST_V  := $(shell jq -r '.ORM.LATEST' < .versions.json)
WORDPROCESSOR_LATEST_V  := $(shell jq -r '.WORDPROCESSOR.LATEST' < .versions.json)
LOCAL_LATEST_V := $(shell jq -r '.LOCAL_LATEST_V' < .versions.json)
DEV_DOCKER_ECR = 825580929289.dkr.ecr.eu-central-1.amazonaws.com
MAIN_DOCKER_ECR = 875551125547.dkr.ecr.eu-central-1.amazonaws.com
DOCKER_HUB = c2dhunilu

test/copy:
	# rm -r tests/_fixtures/a_book/
	cp -R '/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books-Testing/a_book/' tests/_fixtures/
	# echo 'maybe book-content-examples dir can be better utilized'
	cp -R '/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books-Testing/book-content-examples/' tests/_fixtures/
	cp -R '/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books-Testing/split-to-multiple-chapters/' tests/_fixtures/

prep/book:
	mkdir -p /tmp/efs/
	make db/migrate
	DGTMON_NO_WAIT=1 \
		IR_APKG_HTML_BUCKET_NAME=_HTML \
		IR_APKG_MD_BUCKET_NAME=_MARKDOWN \
		METADATA_ASSETS_BUCKET_NAME=_METDATA \
		VERIFIER_MSGS=_WARNINGS \
		python3.12 scripts/prepare_and_build.py book_path="tests/_fixtures/a_book/"

prep/bookv2:
	mkdir -p /tmp/efs/
	make db/migrate
	DGTMON_NO_WAIT=1 \
		IR_APKG_HTML_BUCKET_NAME=_HTML \
		IR_APKG_MD_BUCKET_NAME=_MARKDOWN \
		METADATA_ASSETS_BUCKET_NAME=_METDATA \
		VERIFIER_MSGS=_WARNINGS \
		python3.12 scripts/prepare_and_build.py book_path="tests/_fixtures/a_book/"
	export BUILD_DIR=/tmp/efs/a_book/_build/html
	if [ -d "$BUILD_DIR" ]; then rm -Rf $BUILD_DIR; fi
	(cd /tmp/efs/a_book && myst build --html)
	echo 'npx serve /tmp/efs/a_book/_build/html'

prep/split:
	mkdir -p /tmp/efs/
	make db/migrate
	DGTMON_NO_WAIT=1 \
		IR_APKG_HTML_BUCKET_NAME=_HTML \
		IR_APKG_MD_BUCKET_NAME=_MARKDOWN \
		METADATA_ASSETS_BUCKET_NAME=_METDATA \
		VERIFIER_MSGS=_WARNINGS \
		python3.12 scripts/prepare_and_build.py book_path="tests/_fixtures/split-to-multiple-chapters/"
	export BUILD_DIR=/tmp/efs/split-to-multiple-chapters/_build/html
	if [ -d "$BUILD_DIR" ]; then rm -Rf $BUILD_DIR; fi
	(cd /tmp/efs/split-to-multiple-chapters && myst build --html)
	echo 'npx serve /tmp/efs/split-to-multiple-chapters/_build/html'

test/unit:
	DGTMON_DEBUG=1 python3.12 -m pytest tests/entrypoint tests/orm tests/common/ tests/preparer/ tests/verifier/ tests/builder/ tests/wordprocessor/

test/integration:
	DGTMON_DEBUG=1 python3.12 -m pytest tests/integration/

test:
	DGTMON_DEBUG=1 python3.12 -m pytest tests/entrypoint tests/orm tests/common/ tests/preparer/ tests/verifier/ tests/builder/ tests/wordprocessor/

test/e2e: prep/book test/integration

typecheck:
	mypy src/entrypoint/ --check-untyped-defs
	mypy src/gpu/ --check-untyped-defs
	mypy src/orm/ --check-untyped-defs --explicit-package-bases
	# mypy src/wordprocessor/ --check-untyped-defs

# db/init:
# 	cd src/_common && alembic init migrations

db/makemigrations:
	ls src/_common/migrations/versions
	# 'Enter migration message, best in `01_init_db` format.'
	# cd src/_common && DB_PATH=/tmp/efs/_database.db alembic revision --autogenerate -m  ; cd ../..

db/migrate:
	mkdir -p /tmp/efs
	cd src/_common && DB_PATH=/tmp/efs/_database.db alembic upgrade heads

show/dominique:
	make db/migrate
	DGTMON_NO_WAIT=1 \
		IR_APKG_HTML_BUCKET_NAME=_HTML \
		IR_APKG_MD_BUCKET_NAME=_MARKDOWN \
		METADATA_ASSETS_BUCKET_NAME=_METDATA \
		VERIFIER_MSGS=_WARNINGS \
		python3.12 scripts/prepare_and_build.py book_path="/mnt/c/Users/Pawel.kaminski/OneDrive - University of Luxembourg/Books/a-colonia-luxemburguesa/"

login:
	aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin ${MAIN_DOCKER_ECR}
	aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin ${DEV_DOCKER_ECR}
	docker login --username c2dhadmin

dev/build:
	docker compose build --no-cache

dev/tag:
	docker tag dgtmon-dev-local ${DOCKER_HUB}/dgtmon-dev-local:${LOCAL_LATEST_V}
	docker tag dgtmon-dev-local ${DOCKER_HUB}/dgtmon-dev-local:latest

dev/push:
	docker push ${DOCKER_HUB}/dgtmon-dev-local:${LOCAL_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-local:latest

dev/start:
	docker compose up --detach

dev/test:
	docker compose run main make test

dev/draft:
	# docker compose run main python3.12 scripts/prepare_and_build.py book_path=data/input/$(SLUG)
	docker compose run make test/run

entrypoint/build:
	docker build -t dgtmon-dev-entrypoint src/entrypoint --build-context common=src/_common

entrypoint/tag:
	docker tag dgtmon-dev-entrypoint ${DEV_DOCKER_ECR}/dgtmon-dev-entrypoint:${ENTRYPOINT_LATEST_V}
	docker tag dgtmon-dev-entrypoint ${MAIN_DOCKER_ECR}/dgtmon-dev-entrypoint:${ENTRYPOINT_LATEST_V}
	docker tag dgtmon-dev-entrypoint ${DOCKER_HUB}/dgtmon-dev-entrypoint:${ENTRYPOINT_LATEST_V}

entrypoint/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-entrypoint:${ENTRYPOINT_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-entrypoint:${ENTRYPOINT_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-entrypoint:${ENTRYPOINT_LATEST_V}

entrypoint/make: entrypoint/build entrypoint/tag entrypoint/push

dropbox/build:
	docker build -t dgtmon-dev-dropbox src/dropbox --build-context common=src/_common

dropbox/tag:
	docker tag dgtmon-dev-dropbox ${DEV_DOCKER_ECR}/dgtmon-dev-dropbox:${DROPBOX_LATEST_V}
	docker tag dgtmon-dev-dropbox ${MAIN_DOCKER_ECR}/dgtmon-dev-dropbox:${DROPBOX_LATEST_V}
	docker tag dgtmon-dev-dropbox ${DOCKER_HUB}/dgtmon-dev-dropbox:${DROPBOX_LATEST_V}

dropbox/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-dropbox:${DROPBOX_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-dropbox:${DROPBOX_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-dropbox:${DROPBOX_LATEST_V}

dropbox/make: dropbox/build dropbox/tag dropbox/push

preparer/build:
	docker build -t dgtmon-dev-preparer src/preparer --build-context common=src/_common

preparer/tag:
	docker tag dgtmon-dev-preparer ${DEV_DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_LATEST_V}
	docker tag dgtmon-dev-preparer ${MAIN_DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_LATEST_V}
	docker tag dgtmon-dev-preparer ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_LATEST_V}

preparer/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-preparer:${PREPARER_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-preparer:${PREPARER_LATEST_V}

preparer/make: preparer/build preparer/tag preparer/push

builder/build:
	docker build -t dgtmon-dev-builder src/builder --build-context common=src/_common

builder/tag:
	docker tag dgtmon-dev-builder ${DEV_DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_LATEST_V}
	docker tag dgtmon-dev-builder ${MAIN_DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_LATEST_V}
	docker tag dgtmon-dev-builder ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_LATEST_V}

builder/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-builder:${BUILDER_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-builder:${BUILDER_LATEST_V}

builder/make: builder/build builder/tag builder/push

builderv2/build:
	docker build -t dgtmon-dev-builderv2 src/builderv2

builderv2/tag:
	docker tag dgtmon-dev-builderv2 ${DEV_DOCKER_ECR}/dgtmon-dev-builderv2:${BUILDERv2_LATEST_V}
	docker tag dgtmon-dev-builderv2 ${MAIN_DOCKER_ECR}/dgtmon-dev-builderv2:${BUILDERv2_LATEST_V}
	docker tag dgtmon-dev-builderv2 ${DOCKER_HUB}/dgtmon-dev-builderv2:${BUILDERv2_LATEST_V}

builderv2/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-builderv2:${BUILDERv2_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-builderv2:${BUILDERv2_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-builderv2:${BUILDERv2_LATEST_V}

builderv2/make: builderv2/build builderv2/tag builderv2/push

github/build:
	docker build -t dgtmon-dev-github src/github --build-context common=src/_common

github/tag:
	docker tag dgtmon-dev-github ${DEV_DOCKER_ECR}/dgtmon-dev-github:${GITHUB_LATEST_V}
	docker tag dgtmon-dev-github ${MAIN_DOCKER_ECR}/dgtmon-dev-github:${GITHUB_LATEST_V}
	docker tag dgtmon-dev-github ${DOCKER_HUB}/dgtmon-dev-github:${GITHUB_LATEST_V}

github/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-github:${GITHUB_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-github:${GITHUB_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-github:${GITHUB_LATEST_V}

github/make: github/build github/tag github/push

verifier/build:
	docker build -t dgtmon-dev-verifier src/verifier --build-context common=src/_common

verifier/tag:
	docker tag dgtmon-dev-verifier ${DEV_DOCKER_ECR}/dgtmon-dev-verifier:${VERIFIER_LATEST_V}
	docker tag dgtmon-dev-verifier ${MAIN_DOCKER_ECR}/dgtmon-dev-verifier:${VERIFIER_LATEST_V}
	docker tag dgtmon-dev-verifier ${DOCKER_HUB}/dgtmon-dev-verifier:${VERIFIER_LATEST_V}

verifier/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-verifier:${VERIFIER_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-verifier:${VERIFIER_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-verifier:${VERIFIER_LATEST_V}

verifier/make: verifier/build verifier/tag verifier/push

gpu/build:
	docker build -t dgtmon-dev-gpu src/gpu --build-context common=src/_common

gpu/tag:
	docker tag dgtmon-dev-gpu ${DEV_DOCKER_ECR}/dgtmon-dev-gpu:${GPU_LATEST_V}
	docker tag dgtmon-dev-gpu ${MAIN_DOCKER_ECR}/dgtmon-dev-gpu:${GPU_LATEST_V}
	docker tag dgtmon-dev-gpu ${DOCKER_HUB}/dgtmon-dev-gpu:${GPU_LATEST_V}

gpu/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-gpu:${GPU_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-gpu:${GPU_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-gpu:${GPU_LATEST_V}

gpu/make: gpu/build gpu/tag gpu/push

orm/build:
	docker build -t dgtmon-dev-orm src/orm --build-context common=src/_common

orm/tag:
	docker tag dgtmon-dev-orm ${DEV_DOCKER_ECR}/dgtmon-dev-orm:${ORM_LATEST_V}
	docker tag dgtmon-dev-orm ${MAIN_DOCKER_ECR}/dgtmon-dev-orm:${ORM_LATEST_V}
	docker tag dgtmon-dev-orm ${DOCKER_HUB}/dgtmon-dev-orm:${ORM_LATEST_V}

orm/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-orm:${ORM_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-orm:${ORM_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-orm:${ORM_LATEST_V}

orm/make: orm/build orm/tag orm/push

wordprocessor/build:
	docker build -t dgtmon-dev-wordprocessor src/wordprocessor --build-context common=src/_common

wordprocessor/tag:
	docker tag dgtmon-dev-wordprocessor ${DEV_DOCKER_ECR}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_LATEST_V}
	docker tag dgtmon-dev-wordprocessor ${MAIN_DOCKER_ECR}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_LATEST_V}
	docker tag dgtmon-dev-wordprocessor ${DOCKER_HUB}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_LATEST_V}

wordprocessor/push:
	docker push ${DEV_DOCKER_ECR}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_LATEST_V}
	docker push ${MAIN_DOCKER_ECR}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_LATEST_V}
	docker push ${DOCKER_HUB}/dgtmon-dev-wordprocessor:${WORDPROCESSOR_LATEST_V}

wordprocessor/make: wordprocessor/build wordprocessor/tag wordprocessor/push
