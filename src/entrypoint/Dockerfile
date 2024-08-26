FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}
COPY ./templates ${LAMBDA_TASK_ROOT}

CMD [ "main.lambda_handler" ]
