# 前端快速启动指南

## 🚀 3分钟快速启动

### 步骤 1: 安装依赖
```bash
cd /home/MuyuWorkSpace/01_TrafficProject/Multimodal_RAG_OCR/frontend
npm install
```

### 步骤 2: 配置后端地址

#### 选项 A: 本地部署（前后端都在本机）✅ 推荐
```bash
# 不需要任何配置！
# 默认使用 localhost
npm run dev
```

#### 选项 B: 后端在其他服务器
```bash
# 创建 .env 文件
cat > .env << EOF
VITE_MILVUS_API_URL=http://你的服务器IP:8000
VITE_CHAT_API_URL=http://你的服务器IP:8501
VITE_EXTRACTION_API_URL=http://你的服务器IP:8006
VITE_CHUNK_API_URL=http://你的服务器IP:8001
EOF

npm run dev
```

### 步骤 3: 访问应用
```
打开浏览器访问: http://localhost:5173
```

## 📋 必须修改的配置

### 如果部署在新电脑

只需要修改一个文件（如果后端不在本机）：

**创建 `.env` 文件**:
```bash
# 示例：后端在 192.168.1.100
VITE_MILVUS_API_URL=http://192.168.1.100:8000
VITE_CHAT_API_URL=http://192.168.1.100:8501
VITE_EXTRACTION_API_URL=http://192.168.1.100:8006
VITE_CHUNK_API_URL=http://192.168.1.100:8001
```

**仅此而已！** ✅

## ⚠️ 重要提示

### 已修复的问题
- ✅ `UploadDialog.tsx` 中的 `192.168.110.131` 已改为 `localhost`
- ✅ 所有配置文件都支持环境变量覆盖

### 不需要修改的文件
- ❌ `src/api/config.ts` - 已支持环境变量
- ❌ `src/config.ts` - 已支持环境变量
- ❌ 其他组件 - 都使用配置文件

## 🔄 快速切换环境

### 开发环境
```bash
# 使用 .env (localhost)
npm run dev
```

### 测试环境
```bash
# 使用 .env.test
cp .env.test .env
npm run dev
```

### 生产构建
```bash
# 使用 .env.production
npm run build
# 产物在 dist/ 目录
```

## 🎯 常用命令

```bash
# 开发模式
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview

# 类型检查
npm run type-check
```

## 📝 团队协作

1. **提交模板文件** `env.template` 到 Git
2. **不提交** `.env` 文件（已在 .gitignore）
3. **新成员**只需复制 `env.template` 为 `.env` 并修改地址

## ✨ 就这么简单！

新电脑部署步骤：
1. `npm install`
2. （可选）创建 `.env` 文件
3. `npm run dev`

**默认配置就能在本地运行！** 🎉

