FROM node:22-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /quartz
RUN git clone --depth 1 --branch v4 https://github.com/jackyzha0/quartz.git . \
    && npm ci

RUN sed -i 's/ignorePatterns: \["private", "templates", ".obsidian"\]/ignorePatterns: ["private", "templates", ".obsidian", ".venv", "instructions", "AGENTS.md", "Benvenuto.md", "practice-patterns.md"]/' quartz.config.ts

CMD npx quartz build && cp -r /quartz/public/* /output/
