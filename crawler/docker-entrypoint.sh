#!/bin/bash
set -e

# 创建数据目录软链接
if [ ! -L "/app/data" ]; then
    rm -rf /app/data
    ln -s /data /app/data
fi

# 如果传入参数，直接执行（用于手动运行爬虫）
if [ "$1" = "run" ]; then
    echo "🚀 Running crawler manually..."
    shift
    exec python tools/auto_discover.py "$@"
fi

# 如果传入 once 参数，运行一次后退出
if [ "$1" = "once" ]; then
    echo "🔄 Running crawler once..."
    shift
    python tools/auto_discover.py "$@"
    exit 0
fi

# 默认：启动 cron 服务
echo "⏰ Starting cron service for scheduled crawling..."
echo "📅 Schedule: Daily at 03:00 UTC"
echo "📂 Data path: /data"

# 打印环境变量（隐藏敏感信息）
echo "🔑 API Keys configured:"
[ -n "$PERPLEXITY_API_KEY" ] && echo "  - PERPLEXITY_API_KEY: ****${PERPLEXITY_API_KEY: -4}"

# 启动 cron 并保持前台运行
cron -f
