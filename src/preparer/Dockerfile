FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
COPY mammoth-1.6.1.2-py2.py3-none-any.whl .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

CMD [ "main.lambda_handler" ]
