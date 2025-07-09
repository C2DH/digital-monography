FROM public.ecr.aws/lambda/python:3.12

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE main.staging

WORKDIR /${LAMBDA_TASK_ROOT}

RUN python -m pip install --upgrade pip
COPY requirements.txt .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# RUN pip install -r requirements.txt

COPY manage.py .
# COPY .env .
COPY main ./main
# COPY app ./app
# COPY templates ./templates
# COPY static ./static
# COPY _sqlite3.so .

# RUN python manage.py collectstatic --noinput
# RUN python manage.py makemigrations
# RUN python manage.py migrate
# RUN DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
# RUN python manage.py createsuperuser --noinput || true
# RUN python manage.py test

CMD ["main.wsgi.handler"]
