# JobLens Web Manager

前后端分离的 JobLens 监控管理 Web 页面

## 系统架构

```
前端(Vue 3) → Python后端代理 → 注册中心(8080) / 采集器(7592)
```

## 技术栈

### 后端
- **框架**: FastAPI
- **HTTP客户端**: httpx
- **数据验证**: Pydantic

### 前端
- **框架**: Vue 3 + TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **HTTP客户端**: Axios

## 项目结构

```
joblens_web_manager/
├── backend/                      # Python后端代理
│   ├── backend/
│   │   ├── main.py              # FastAPI主应用
│   │   ├── config.py            # 配置文件
│   │   ├── models/              # Pydantic数据模型
│   │   ├── routers/             # API路由
│   │   └── services/            # 业务逻辑
│   ├── requirements.txt         # Python依赖
│   └── .env                     # 环境变量
├── frontend/                    # Vue前端
│   ├── src/
│   │   ├── api/                # API接口
│   │   ├── views/              # 页面视图
│   │   ├── router/             # 路由配置
│   │   └── main.ts             # 入口文件
│   ├── package.json
│   └── .env                    # 环境变量
├── app.py                       # JobLens采集器
└── JSRC.py                      # JobLens服务注册中心
```

## 功能特性

### 1. 服务管理
- 查看所有注册的服务节点
- 查看服务健康状态（注册中心 + 采集器）
- 注销服务
- 注册中心状态监控

### 2. 作业管理
- 查看跨所有服务的作业列表
- 添加新作业（支持普通作业和Condor作业）
- 删除作业
- 查看作业详情

### 3. 监控大盘
- 服务状态统计（总数、健康、异常、活跃）
- 服务状态分布图表
- 最近服务列表
- 注册中心健康状态

### 4. 性能监控
- 采集器性能统计（采集数、平均时间、错误数）
- Writer性能统计（写入数、平均时间、缓冲区）
- Prometheus格式指标
- 作业数量统计

## 安装和运行

### 后端

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量（编辑 `.env` 文件）：
```env
REGISTRY_URL=http://localhost:8080
COLLECTOR_TIMEOUT=5.0
CACHE_TTL=30
```

3. 运行后端：
```bash
uvicorn backend.main:app --reload --port 8000
```

4. 访问API文档：
```
http://localhost:8000/docs
```

### 前端

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 配置环境变量（编辑 `.env` 文件）：
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_REFRESH_INTERVAL=30000
```

3. 运行前端：
```bash
npm run dev
```

4. 访问页面：
```
http://localhost:5173
```

## API接口

### 服务管理
- `GET /api/services` - 获取服务列表
- `GET /api/services/{id}` - 获取服务详情
- `GET /api/services/{id}/health` - 获取服务健康状态
- `DELETE /api/services/{id}` - 注销服务
- `GET /api/services/registry/health` - 注册中心健康状态
- `GET /api/services/registry/stats` - 注册中心统计

### 作业管理
- `GET /api/jobs` - 获取所有作业
- `GET /api/jobs/{id}` - 获取作业详情
- `POST /api/jobs` - 创建作业
- `DELETE /api/jobs/{id}` - 删除作业
- `GET /api/jobs/{service_id}/count` - 获取作业数量

### 监控指标
- `GET /api/metrics/services/{id}/collectors` - 采集器性能
- `GET /api/metrics/services/{id}/writers` - Writer性能
- `GET /api/metrics/services/{id}/all` - 所有指标
- `GET /api/metrics/services/{id}/prometheus` - Prometheus指标
- `GET /api/metrics/registry` - 注册中心指标

## 配置说明

### 后端配置

在 `backend/.env` 中配置：
- `REGISTRY_URL`: 注册中心地址
- `COLLECTOR_TIMEOUT`: 采集器请求超时时间（秒）
- `CACHE_TTL`: 缓存时间（秒）

### 前端配置

在 `frontend/.env` 中配置：
- `VITE_API_BASE_URL`: 后端API地址
- `VITE_REFRESH_INTERVAL`: 自动刷新间隔（毫秒）

## 开发说明

### 后端开发

1. 数据模型在 `backend/models/` 目录
2. API路由在 `backend/routers/` 目录
3. 业务逻辑在 `backend/services/` 目录
4. 使用 FastAPI 的依赖注入和异步支持

### 前端开发

1. API接口在 `src/api/` 目录
2. 页面视图在 `src/views/` 目录
3. 使用 Element Plus 组件库
4. 使用 Pinia 进行状态管理
5. 使用 ECharts 进行数据可视化

## 注意事项

1. 所有请求都经过Python后端代理，不直接访问注册中心和采集器
2. 后端会自动处理多个采集器节点的请求
3. 页面会自动刷新（默认30秒）
4. 支持响应式布局，适配不同屏幕尺寸
5. 敏感操作（注销服务、删除作业）需要确认

## 故障排查

### 后端无法连接注册中心
- 检查 `REGISTRY_URL` 配置是否正确
- 确保注册中心服务正在运行
- 检查网络连接

### 前端无法连接后端
- 检查 `VITE_API_BASE_URL` 配置是否正确
- 确保后端服务正在运行
- 检查CORS配置

### 作业管理失败
- 检查目标服务是否健康
- 检查作业参数是否正确
- 查看后端日志获取详细信息
