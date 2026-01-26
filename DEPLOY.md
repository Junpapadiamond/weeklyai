# WeeklyAI 部署指南

## 🐳 Docker 部署 (推荐)

### 前提条件

- Docker 20.10+
- Docker Compose 2.0+
- Git

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/WeeklyAI.git
cd WeeklyAI

# 2. 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入 API Keys

# 3. 初始化数据 (首次部署)
mkdir -p crawler/data
cp -r crawler/data/* /var/lib/weeklyai/data/  # 或使用 Docker volume

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | 前端页面 |
| Backend | 5000 | API 服务 |
| Crawler | - | 定时任务 (无端口) |

### 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f crawler

# 手动运行爬虫
docker-compose run --rm crawler run --region all --type mixed

# 只运行一次爬虫 (不启动 cron)
docker-compose run --rm crawler once --region us

# 重启服务
docker-compose restart

# 更新镜像并重启
docker-compose pull
docker-compose up -d

# 停止并清理
docker-compose down
docker-compose down -v  # 同时删除数据卷
```

---

## 🚀 GitHub Actions CI/CD

### 配置 Secrets

在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加:

| Secret | 说明 |
|--------|------|
| `PERPLEXITY_API_KEY` | Perplexity API Key |
| `SERVER_HOST` | 服务器地址 (可选) |
| `SERVER_USER` | SSH 用户名 (可选) |
| `SERVER_SSH_KEY` | SSH 私钥 (可选) |

### 工作流程

1. **Push 到 main**: 自动构建并推送镜像到 GitHub Container Registry
2. **定时任务**: 每天 UTC 19:00 (北京时间 03:00) 自动运行爬虫
3. **手动触发**: 可在 Actions 页面手动运行爬虫或部署

### 手动触发爬虫

1. 进入 GitHub 仓库 → Actions
2. 选择 "CI/CD Pipeline"
3. 点击 "Run workflow"
4. 勾选 "Run crawler to update data"
5. 点击 "Run workflow"

---

## ☁️ 云平台部署

### Railway

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录并部署
railway login
railway init
railway up
```

### Render

1. 连接 GitHub 仓库
2. 创建 3 个 Web Service (frontend, backend, crawler)
3. 配置环境变量
4. 自动部署

### Fly.io

```bash
# 安装 flyctl
curl -L https://fly.io/install.sh | sh

# 部署
fly launch
fly deploy
```

---

## 🔧 服务器部署 (VPS)

### 使用 Docker Compose

```bash
# SSH 到服务器
ssh user@your-server.com

# 安装 Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 克隆并部署
git clone https://github.com/your-username/WeeklyAI.git /opt/weeklyai
cd /opt/weeklyai
cp env.example .env
nano .env  # 编辑环境变量

# 启动
docker-compose up -d
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name weeklyai.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL 证书 (Let's Encrypt)

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d weeklyai.example.com
```

---

## 📊 数据管理

### 数据备份

```bash
# 备份数据卷
docker run --rm -v weeklyai_weeklyai-data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v weeklyai_weeklyai-data:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /data
```

### 数据更新流程

1. 爬虫运行 → 数据写入 `/data/products_featured.json`
2. 后端 API 读取 → 返回最新数据
3. 前端请求 API → 展示最新产品

无需重启服务，数据自动更新！

---

## 🔍 故障排除

### 常见问题

**Q: 前端显示"后端无法访问"**
```bash
# 检查后端是否运行
docker-compose ps backend
docker-compose logs backend
```

**Q: 爬虫没有更新数据**
```bash
# 查看爬虫日志
docker-compose logs crawler
cat crawler/logs/cron.log
```

**Q: API Key 无效**
```bash
# 检查环境变量
docker-compose exec crawler env | grep API_KEY
```

### 健康检查

```bash
# 检查所有服务健康状态
docker-compose ps

# 测试 API
curl http://localhost:5000/api/v1/products/weekly-top?limit=1

# 测试前端
curl http://localhost:3000
```

---

## 📈 监控 (可选)

### 添加 Prometheus + Grafana

```yaml
# 在 docker-compose.yml 中添加
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

*最后更新: 2026-01-20*
