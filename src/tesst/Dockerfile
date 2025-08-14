FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

# # Copy contents of the shared "src/_common" directory to /var/task/
# RUN --mount=from=common,target=common \
#     cp -r common/* ${LAMBDA_TASK_ROOT}
# Copy contents of the shared "src/_common" directory to /var/task/src/_common/
RUN mkdir -p ${LAMBDA_TASK_ROOT}/src/_common
RUN --mount=from=common,target=common \
    cp -r common/* ${LAMBDA_TASK_ROOT}/src/_common/

CMD [ "main.lambda_handler" ]
