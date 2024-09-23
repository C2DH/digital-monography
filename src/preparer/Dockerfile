FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y git

# RUN set -ex \
#    && dnf install -y tar gzip \
#    && GIT_VERSION=2.41.0 \
#    && GIT_TAR_FILE=git-$GIT_VERSION.tar.gz \
#    && GIT_SRC=https://github.com/git/git/archive/v${GIT_VERSION}.tar.gz  \
#    && curl -L -o $GIT_TAR_FILE $GIT_SRC \
#    && tar zxf $GIT_TAR_FILE \
#    && cd git-$GIT_VERSION \
#    && make -j4 prefix=/usr \
#    && make install prefix=/usr \
#    && cd .. && rm -rf git-$GIT_VERSION \
#    && rm -rf $GIT_TAR_FILE /tmp/*

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

CMD [ "main.lambda_handler" ]
