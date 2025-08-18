FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

# Copy contents of the shared "src/_common" directory to /var/task/src/_common/
RUN mkdir -p ${LAMBDA_TASK_ROOT}/src/_common
RUN --mount=from=common,target=common \
    cp -r common/status.py ${LAMBDA_TASK_ROOT}/src/_common/status.py \
    cp -r common/constants.py ${LAMBDA_TASK_ROOT}/src/_common/constants.py \
    cp -r common/keys.py ${LAMBDA_TASK_ROOT}/src/_common/keys.py \
    cp -r common/github_trigger.py ${LAMBDA_TASK_ROOT}/src/_common/github_trigger.py

CMD [ "main.lambda_handler" ]
