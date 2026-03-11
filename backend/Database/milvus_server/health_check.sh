#!/bin/bash

# Milvus 健康检查脚本
# 防止 etcd WAL 日志疯涨事故重演 (2026-03-02 111GB 事故)
# 每 30 分钟检查一次，超过阈值自动告警和清理

set -e

# ============ 配置 ============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/health_check.log"
MEMORY_LOG="${SCRIPT_DIR}/../../memory/milvus-health-log.md"
ALERT_THRESHOLD_GB=10
CLEANUP_THRESHOLD_GB=5
MILVUS_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yaml"

# 告警通知配置 (飞书群 webhook)
FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-}"  # 可选：设置 webhook 发送告警

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============ 函数 ============

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} $1" | tee -a "$LOG_FILE"
}

log_color() {
    local color=$1
    local msg=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} ${color}${msg}${NC}" | tee -a "$LOG_FILE"
}

# 获取目录大小 (返回 MB)
get_dir_size_mb() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo "0"
        return
    fi
    # macOS 兼容的 du 命令
    local size_kb=$(du -sk "$dir" 2>/dev/null | cut -f1)
    echo $((size_kb / 1024))
}

# 检查 Docker 是否可用
check_docker() {
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "🐳 检查 Docker 状态..."
    
    if ! command -v docker &> /dev/null; then
        log_color "$RED" "❌ Docker 未安装，无法检查 Milvus 容器状态"
        return 1
    fi
    
    if ! docker info &> /dev/null 2>&1; then
        log_color "$RED" "❌ Docker 未运行"
        return 1
    fi
    
    log_color "$GREEN" "✓ Docker 运行正常"
    return 0
}

# 检查容器状态
check_containers() {
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "📦 检查容器状态..."
    
    local all_healthy=true
    
    # 使用 docker compose 检查
    if [ -f "$MILVUS_COMPOSE_FILE" ]; then
        local compose_output=$(docker compose -f "$MILVUS_COMPOSE_FILE" ps 2>/dev/null || echo "")
        
        if [ -n "$compose_output" ]; then
            log "Docker Compose 服务状态:"
            echo "$compose_output" | grep -v "^$" | while read line; do
                if echo "$line" | grep -q "running\|Up"; then
                    log_color "$GREEN" "  ✓ $line"
                elif echo "$line" | grep -q "Exit\|exited"; then
                    log_color "$RED" "  ❌ $line"
                    all_healthy=false
                else
                    log "  $line"
                fi
            done
        fi
    fi
    
    # 检查独立容器
    for container in milvus-etcd milvus-minio milvus-standalone; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
            if [ "$status" = "running" ]; then
                log_color "$GREEN" "  ✓ $container: 运行中"
            else
                log_color "$YELLOW" "  ⚠️  $container: $status"
                all_healthy=false
            fi
        else
            log_color "$YELLOW" "  ○ $container: 未找到"
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        log_color "$GREEN" "✅ 所有容器健康"
    else
        log_color "$YELLOW" "⚠️  部分容器异常"
    fi
    
    return 0
}

# 检查目录大小
check_directory_size() {
    local dir=$1
    local name=$2
    local threshold_gb=$3
    
    if [ ! -d "$dir" ]; then
        log_color "$YELLOW" "  ○ $name: 目录不存在"
        return 0
    fi
    
    # 获取目录大小 (MB)
    local size_mb=$(get_dir_size_mb "$dir")
    local size_gb=$((size_mb / 1024))
    local threshold_mb=$((threshold_gb * 1024))
    local warning_mb=$((threshold_mb / 2))
    
    # 检查是否超过阈值
    if [ "$size_mb" -gt "$threshold_mb" ]; then
        log_color "$RED" "  🔴 $name: ${size_gb}GB (超过 ${threshold_gb}GB 阈值!)"
        return 1
    elif [ "$size_mb" -gt "$warning_mb" ]; then
        log_color "$YELLOW" "  ⚠️  $name: ${size_gb}GB (接近阈值)"
        return 0
    else
        log_color "$GREEN" "  ✓ $name: ${size_gb}GB (${size_mb}MB)"
        return 0
    fi
}

# 检查 volumes 目录大小
check_volumes() {
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "💾 检查存储目录大小..."
    
    local volumes_dir="${SCRIPT_DIR}/volumes"
    local has_warning=false
    
    # etcd 数据目录
    check_directory_size "${volumes_dir}/etcd" "etcd 数据" "$ALERT_THRESHOLD_GB" || has_warning=true
    
    # MinIO 数据目录
    check_directory_size "${volumes_dir}/minio" "MinIO 数据" "$ALERT_THRESHOLD_GB" || has_warning=true
    
    # Milvus 数据目录
    check_directory_size "${volumes_dir}/milvus" "Milvus 数据" "$ALERT_THRESHOLD_GB" || has_warning=true
    
    # 单独检查 etcd WAL 日志
    local wal_dir="${volumes_dir}/etcd/member/wal"
    if [ -d "$wal_dir" ]; then
        local wal_size_mb=$(get_dir_size_mb "$wal_dir")
        local wal_size_gb=$((wal_size_mb / 1024))
        local cleanup_mb=$((CLEANUP_THRESHOLD_GB * 1024))
        
        if [ "$wal_size_mb" -gt "$cleanup_mb" ]; then
            log_color "$RED" "  🔴 etcd WAL 日志：${wal_size_gb}GB (超过 ${CLEANUP_THRESHOLD_GB}GB，需要清理!)"
            cleanup_etcd_wal
            has_warning=true
        else
            log_color "$GREEN" "  ✓ etcd WAL 日志：${wal_size_mb}MB"
        fi
    else
        log_color "$YELLOW" "  ○ etcd WAL 目录：不存在"
    fi
    
    if [ "$has_warning" = true ]; then
        log_color "$YELLOW" "⚠️  存储警告：部分目录超过阈值"
        send_alert "Milvus 存储警告：部分目录超过 ${ALERT_THRESHOLD_GB}GB 阈值"
        return 1
    else
        log_color "$GREEN" "✅ 存储空间正常"
        return 0
    fi
}

# 清理 etcd WAL 日志
cleanup_etcd_wal() {
    log_color "$YELLOW" "🧹 开始清理 etcd WAL 日志..."
    
    local wal_dir="${SCRIPT_DIR}/volumes/etcd/member/wal"
    
    if [ ! -d "$wal_dir" ]; then
        log_color "$YELLOW" "  WAL 目录不存在，跳过清理"
        return 0
    fi
    
    # 方法 1: 删除旧的 WAL 文件 (保留最近 3 个)
    log "  保留最近 3 个 WAL 文件，删除旧文件..."
    local wal_count=$(ls -1 "${wal_dir}"/*.wal 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$wal_count" -gt 3 ]; then
        local files_to_delete=$((wal_count - 3))
        local freed_mb=0
        
        # 获取最旧的文件并删除
        ls -t "${wal_dir}"/*.wal 2>/dev/null | tail -n +4 | while read file; do
            if [ -f "$file" ]; then
                local file_size_kb=$(du -sk "$file" 2>/dev/null | cut -f1)
                rm -f "$file"
                log "  删除：$(basename "$file")"
            fi
        done
        
        log_color "$GREEN" "  ✓ 清理完成，保留 3 个最新 WAL 文件"
    else
        log "  WAL 文件数量：$wal_count (无需清理)"
    fi
    
    # 方法 2: 触发 etcd snapshot (如果容器运行)
    if docker ps --format '{{.Names}}' | grep -q "milvus-etcd"; then
        log "  尝试触发 etcd snapshot..."
        docker exec milvus-etcd etcdctl snapshot save /tmp/etcd-snapshot-$(date +%Y%m%d-%H%M%S).db 2>/dev/null || log "  snapshot 跳过"
    fi
    
    log_color "$GREEN" "✅ etcd WAL 清理完成"
    return 0
}

# 发送告警到飞书群
send_alert() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    log_color "$YELLOW" "📢 发送告警：$message"
    
    if [ -n "$FEISHU_WEBHOOK" ]; then
        local payload="{
            \"msg_type\": \"text\",
            \"content\": {
                \"text\": \"🔴 Milvus 健康告警\\n时间：${timestamp}\\n\\n${message}\\n\\n请立即检查：~/projects/demo/Multimodal_RAG/backend/Database/milvus_server/\"
            }
        }"
        
        curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$FEISHU_WEBHOOK" > /dev/null 2>&1
        log "  告警已发送到飞书群"
    else
        log_color "$YELLOW" "  ⚠️  FEISHU_WEBHOOK 未设置，告警仅记录到日志"
    fi
}

# 记录健康数据到 memory 文件
log_to_memory() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local memory_file="${MEMORY_LOG}"
    
    # 创建 memory 目录
    mkdir -p "$(dirname "$memory_file")"
    
    # 如果文件不存在，创建并添加标题
    if [ ! -f "$memory_file" ]; then
        cat > "$memory_file" << EOF
# Milvus 健康检查日志

> 📊 自动监控记录 - 防止 etcd WAL 日志疯涨事故重演

## 监控配置

- **检查频率**: 每 30 分钟
- **告警阈值**: ${ALERT_THRESHOLD_GB}GB
- **自动清理阈值**: ${CLEANUP_THRESHOLD_GB}GB
- **创建时间**: ${timestamp}

---

## 检查记录

EOF
    fi
    
    # 添加新的检查记录
    local status_text="✅ 正常"
    local volumes_dir="${SCRIPT_DIR}/volumes"
    
    cat >> "$memory_file" << EOF

### ${timestamp}

**状态**: ${status_text}

**存储使用情况**:
EOF
    
    # 添加各目录大小
    for dir in etcd minio milvus; do
        if [ -d "${volumes_dir}/${dir}" ]; then
            local size=$(du -sh "${volumes_dir}/${dir}" 2>/dev/null | cut -f1)
            echo "- ${dir}: ${size}" >> "$memory_file"
        else
            echo "- ${dir}: 不存在" >> "$memory_file"
        fi
    done
    
    echo "" >> "$memory_file"
    echo "---" >> "$memory_file"
    echo "" >> "$memory_file"
}

# 主函数
main() {
    log "========================================"
    log_color "$BLUE" "🏥 Milvus 健康检查开始"
    log "========================================"
    
    local exit_code=0
    
    # 1. 检查 Docker
    check_docker || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        # 2. 检查容器状态
        check_containers || exit_code=1
        
        # 3. 检查存储目录
        check_volumes || exit_code=1
    fi
    
    # 4. 记录到 memory 文件
    log_to_memory
    
    log "========================================"
    if [ $exit_code -eq 0 ]; then
        log_color "$GREEN" "✅ Milvus 健康检查完成 - 一切正常"
    else
        log_color "$YELLOW" "⚠️  Milvus 健康检查完成 - 发现警告"
    fi
    log "========================================"
    
    return $exit_code
}

# 执行
main "$@"
