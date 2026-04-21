FROM node:22-slim AS builder

# Installa git (necessario per clonare Quartz)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clona Quartz v4
WORKDIR /quartz
RUN git clone --depth 1 --branch v4 https://github.com/jackyzha0/quartz.git . \
    && npm ci

RUN node -e "const fs=require('fs');const path='quartz.config.ts';let text=fs.readFileSync(path,'utf8');text=text.replace(/enableSPA:\\s*true,/,'enableSPA: false,');text=text.replace(/analytics:\\s*\\{[\\s\\S]*?\\},/,'analytics: null,');text=text.replace(/ignorePatterns:\\s*\\[[^\\]]*\\]/,'ignorePatterns: [\"private\", \"templates\", \".obsidian\", \".venv\", \"instructions\", \"AGENTS.md\", \"Benvenuto.md\", \"practice-patterns.md\"]');text=text.replace(/priority:\\s*\\[[^\\]]*\\]/,'priority: [\"frontmatter\", \"filesystem\"]');fs.writeFileSync(path,text);"

# Copia il contenuto del vault Obsidian
COPY ./Praxis-ql/ /quartz/content/

# Build del sito statico
RUN npx quartz build

# --- Stage 2: serve con un web server leggero ---
FROM nginx:alpine

# Copia il sito generato
COPY --from=builder /quartz/public /usr/share/nginx/html

# Configurazione Nginx per URL senza estensione .html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
