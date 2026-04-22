FROM node:22-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /quartz
RUN git clone --depth 1 --branch v4 https://github.com/jackyzha0/quartz.git . \
    && npm ci

RUN node -e "const fs=require('fs');const path='quartz.config.ts';let text=fs.readFileSync(path,'utf8');text=text.replace(/enableSPA:\\s*true,/,'enableSPA: false,');text=text.replace(/analytics:\\s*\\{[\\s\\S]*?\\},/,'analytics: null,');text=text.replace(/ignorePatterns:\\s*\\[[^\\]]*\\]/,'ignorePatterns: [\"private\", \"templates\", \".obsidian\", \".venv\", \"instructions\", \"AGENTS.md\", \"Benvenuto.md\", \"practice-patterns.md\"]');text=text.replace(/priority:\\s*\\[[^\\]]*\\]/,'priority: [\"frontmatter\", \"filesystem\"]');fs.writeFileSync(path,text);"

COPY scripts/patch_quartz_graph_colors.js /tmp/patch_quartz_graph_colors.js
RUN node /tmp/patch_quartz_graph_colors.js

CMD sh -lc 'npx quartz build && find /output -mindepth 1 -maxdepth 1 -exec rm -rf {} + && cp -r /quartz/public/* /output/ && if [ -d /quartz/content/viz ]; then mkdir -p /output/viz && cp -r /quartz/content/viz/* /output/viz/; fi'
