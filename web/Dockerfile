FROM node:20-alpine AS dev
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm ci
COPY . .
RUN npm run build

# Прод-статика: собирает dist и отдаёт его в общий volume для Caddy.
# VITE_API_URL подставляется на сборке (в проде — "/api").
FROM node:20-alpine AS dist
WORKDIR /app
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
COPY package.json ./
RUN npm ci
COPY . .
RUN npm run build
VOLUME ["/srv"]
CMD ["sh", "-c", "rm -rf /srv/* && cp -r /app/dist/* /srv/ && sleep infinity"]
