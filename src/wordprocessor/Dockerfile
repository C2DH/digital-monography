FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY ./*.py ${LAMBDA_TASK_ROOT}

CMD [ "main.lambda_handler" ]

#### Maybe TypeScript??? ####
# FROM public.ecr.aws/lambda/nodejs:22 as builder
# WORKDIR /usr/app
# COPY package.json main.ts  ./
# RUN npm install
# RUN npm run build

# FROM public.ecr.aws/lambda/nodejs:22
# WORKDIR ${LAMBDA_TASK_ROOT}
# COPY --from=builder /usr/app/dist/* ./
# CMD ["main.lambda_handler"]
