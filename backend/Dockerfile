# 后端 Dockerfile
# 使用 Python 3.13 官方镜像
FROM python:3.13-slim AS builder

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 写入 pyc 文件和缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（包括构建 Python 包所需的工具）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.13-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 从构建阶段复制已安装的 Python 包
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制后端代码
COPY backend/ ./backend/

# 复制可能存在的 .env 文件（如果存在）
# COPY .env ./

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]