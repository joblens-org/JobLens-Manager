# 前端 Dockerfile
# 第一阶段：构建阶段
FROM node:22.22 AS builder

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖（包括开发依赖，构建需要）
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 第二阶段：nginx 服务
FROM nginx:alpine-slim

# 复制构建产物到 nginx 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制配置模板
COPY public/config.js.template /usr/share/nginx/html/config.js

# 创建启动脚本，用于替换配置占位符
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'echo "替换运行时配置..."' >> /docker-entrypoint.sh && \
    echo 'sed -i "s|{{VITE_API_BASE_URL}}|${VITE_API_BASE_URL:-http://localhost:8000/api}|g" /usr/share/nginx/html/config.js' >> /docker-entrypoint.sh && \
    echo 'sed -i "s|{{VITE_REFRESH_INTERVAL}}|${VITE_REFRESH_INTERVAL:-30000}|g" /usr/share/nginx/html/config.js' >> /docker-entrypoint.sh && \
    echo 'sed -i "s|{{VITE_API_TIMEOUT}}|${VITE_API_TIMEOUT:-30000}|g" /usr/share/nginx/html/config.js' >> /docker-entrypoint.sh && \
    echo 'sed -i "s|{{VITE_SERVICE_DETAIL_REFRESH_INTERVAL}}|${VITE_SERVICE_DETAIL_REFRESH_INTERVAL:-5000}|g" /usr/share/nginx/html/config.js' >> /docker-entrypoint.sh && \
    echo 'echo "配置替换完成，启动 nginx..."' >> /docker-entrypoint.sh && \
    echo 'nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 80

# 启动 nginx（使用自定义启动脚本）
CMD ["/docker-entrypoint.sh"]