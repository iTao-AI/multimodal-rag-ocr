#!/bin/bash
# backend/health_check.sh
# 健康检查脚本 — 等待所有服务就绪

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
MAX_RETRIES=${HEALTH_CHECK_RETRIES:-30}
RETRY_INTERVAL=${HEALTH_CHECK_INTERVAL:-2}

# 服务列表: 名称:端口:健康端点
SERVICES=(
    "pdf_extraction:8006:/health"
    "text_chunking:8001:/health"
    "milvus_api:8000:/health"
    "chat:8501:/health"
)

# 检查单个服务
check_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    local attempt=1

    while [ $attempt -le $MAX_RETRIES ]; do
        if curl -sf "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $name 就绪 (${attempt}s)"
            return 0
        fi
        sleep $RETRY_INTERVAL
        attempt=$((attempt + 1))
    done

    echo -e "  ${RED}✗${NC} $name 启动超时 (${MAX_RETRIES} 次重试)"
    return 1
}

# 主流程
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  健康检查 — 等待所有服务就绪${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

FAILED=0
for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port endpoint <<< "$service"
    echo -e "${YELLOW}检查 $name (port:$port)...${NC}"
    if ! check_service "$name" "$port" "$endpoint"; then
        FAILED=1
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  所有服务已就绪${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  部分服务启动失败${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
