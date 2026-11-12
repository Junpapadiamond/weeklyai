# Build from the repository root: docker build -f crawler/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY crawler/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY crawler/ .
# The crawler wrapper resolves its single shared implementation at /backend.
COPY backend/product_identity.py /backend/product_identity.py
RUN python -c "from utils.product_identity import hosted_project_key; assert hosted_project_key('https://github.com/RLinf/RPent') == 'github.com/rlinf/rpent'"

# 创建日志目录
RUN mkdir -p /app/logs /data

# 设置 cron 任务 (每天凌晨 3 点运行)
RUN echo "0 3 * * * cd /app && python tools/auto_discover.py --region all --type mixed >> /app/logs/cron.log 2>&1" > /etc/cron.d/crawler-cron \
    && chmod 0644 /etc/cron.d/crawler-cron \
    && crontab /etc/cron.d/crawler-cron

# 环境变量
ENV DATA_PATH=/data
ENV PYTHONUNBUFFERED=1

# 启动脚本
COPY crawler/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
