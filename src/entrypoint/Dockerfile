FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}
COPY /admin ${LAMBDA_TASK_ROOT}/admin
COPY /assets ${LAMBDA_TASK_ROOT}/assets
COPY /citations ${LAMBDA_TASK_ROOT}/citations
COPY /cloud ${LAMBDA_TASK_ROOT}/cloud
COPY /dbx ${LAMBDA_TASK_ROOT}/dbx
COPY /headings ${LAMBDA_TASK_ROOT}/headings

# Copy contents of the shared "src/_common" directory to /var/task/src/_common/
RUN mkdir -p ${LAMBDA_TASK_ROOT}/src/_common
RUN --mount=from=common,target=common \
    cp -r common/* ${LAMBDA_TASK_ROOT}/src/_common/

CMD [ "main.lambda_handler" ]
