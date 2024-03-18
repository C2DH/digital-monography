setup:
	. .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -r .local-requirements.txt 

lint:
	flake8 src --exclude .venv; mypy src --exclude .venv

plan:
	cd infra/ && terraform plan --var-file=../secrets/local.tfvars

apply:
	cd infra/ && terraform apply --var-file=../secrets/local.tfvars

zip:
	./src/builder/prep_deps.sh
	./src/preparer/prep_deps.sh

test:
	# export UPLOAD_APKG_BUCKET_NAME=$(terraform output upload_apkg_bucket_name)
	python -m pytest -vv tests/

list-logs:
	aws logs describe-log-streams --endpoint-url=http://localhost:4566 --log-group-name /aws/lambda/builder

get-log:
	aws logs get-log-events --endpoint-url=http://localhost:4566 --log-group-name /aws/lambda/builder --log-stream-name ${stream} 

destroy:
	cd infra/ && terraform destroy --var-file=../secrets/local.tfvars

