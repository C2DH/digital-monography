FROM public.ecr.aws/lambda/python:3.12

ENV TZ=UTC

RUN dnf install -y \
    glibc \
    groff \
    less

RUN dnf install -y unzip && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

CMD [ "main.lambda_handler" ]
