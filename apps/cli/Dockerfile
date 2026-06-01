FROM node:20-alpine

WORKDIR /app

COPY package.json yarn.lock ./
COPY tsconfig.json ./
COPY bin ./bin
COPY src ./src

RUN corepack enable \
    && yarn install \
    && yarn build \
    && chmod +x ./bin/chat ./bin/xninetzy

ENTRYPOINT ["./bin/xninetzy"]
