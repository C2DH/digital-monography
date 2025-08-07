FROM public.ecr.aws/lambda/nodejs:22 as builder

ENV TZ=UTC

WORKDIR /usr/app
COPY package.json main.ts  ./
RUN npm install
RUN npx esbuild main.ts --bundle --platform=node --target=node14 --outfile=dist/main.js

FROM public.ecr.aws/lambda/nodejs:22
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder /usr/app/dist/* ./

CMD [ "main.lambda_handler" ]
