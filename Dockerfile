FROM node:22-slim AS builder

# Installa git (necessario per clonare Quartz)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clona Quartz v4
WORKDIR /quartz
RUN git clone --depth 1 --branch v4 https://github.com/jackyzha0/quartz.git . \
    && npm ci

# Copia il contenuto del vault Obsidian
COPY ./#qtimes/ /quartz/content/

# Build del sito statico
RUN npx quartz build

# --- Stage 2: serve con un web server leggero ---
FROM nginx:alpine

# Copia il sito generato
COPY --from=builder /quartz/public /usr/share/nginx/html

EXPOSE 80
