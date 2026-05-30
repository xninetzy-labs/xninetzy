FROM node:20-alpine AS deps

WORKDIR /app

RUN corepack enable

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY tsconfig.json ./
COPY src ./src
RUN yarn build

FROM node:20-alpine

WORKDIR /app

RUN corepack enable

COPY package.json yarn.lock ./
RUN yarn install --production --frozen-lockfile

COPY --from=deps /app/dist ./dist

CMD ["node", "dist/app.js"]
