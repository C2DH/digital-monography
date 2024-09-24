FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y git

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

CMD [ "main.lambda_handler" ]
