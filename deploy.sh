#!/bin/bash
# ========================================
# 银发通 一键部署脚本
# 在 ECS 服务器上执行: bash deploy.sh
# ========================================

set -e

echo "=========================================="
echo "  银发通 阿里云 ECS 部署"
echo "=========================================="

# 1. 安装 Docker
echo "[1/6] 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "  → 安装 Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    echo "  ✓ Docker 安装完成"
else
    echo "  ✓ Docker 已安装: $(docker --version)"
fi

# 2. 安装 Docker Compose
echo "[2/6] 检查 Docker Compose..."
if ! docker compose version &> /dev/null; then
    echo "  → 安装 Docker Compose 插件..."
    apt-get update && apt-get install -y docker-compose-plugin 2>/dev/null || \
    yum install -y docker-compose-plugin 2>/dev/null || {
        echo "  → 自动安装失败，尝试手动安装..."
        mkdir -p ~/.docker/cli-plugins/
        curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
            -o ~/.docker/cli-plugins/docker-compose
        chmod +x ~/.docker/cli-plugins/docker-compose
    }
    echo "  ✓ Docker Compose 安装完成"
else
    echo "  ✓ Docker Compose 已安装"
fi

# 3. 配置生产 .env
echo "[3/6] 配置生产环境变量..."
if [ -f .env.production ]; then
    cp .env.production .env
    # 生成随机 JWT_SECRET_KEY
    JWT_KEY=$(openssl rand -base64 48)
    sed -i "s|JWT_SECRET_KEY=CHANGE_ME_ON_DEPLOY|JWT_SECRET_KEY=${JWT_KEY}|" .env
    echo "  ✓ .env 已生成（JWT_SECRET_KEY 已随机生成）"
else
    echo "  ✗ .env.production 文件不存在！"
    exit 1
fi

# 4. 备份 override 文件（开发用，生产不需要）
echo "[4/6] 清理开发配置..."
if [ -f docker-compose.override.yml ]; then
    mv docker-compose.override.yml docker-compose.override.yml.dev.bak
    echo "  ✓ docker-compose.override.yml 已备份"
fi

# 5. 构建并启动
echo "[5/6] 构建镜像并启动容器（首次约 3-5 分钟）..."
docker compose up -d --build

# 6. 等待健康检查
echo "[6/6] 等待服务就绪..."
echo ""
echo "  查看状态: docker compose ps"
echo "  查看日志: docker compose logs -f"
echo ""
echo "=========================================="
echo "  部署完成！访问 http://59.110.149.107"
echo "=========================================="
echo ""
echo "  后续步骤:"
echo "  1. docker compose ps          # 确认所有容器 healthy"
echo "  2. curl http://localhost/      # 验证后端"
echo "  3. 浏览器打开 http://59.110.149.107"
echo ""
