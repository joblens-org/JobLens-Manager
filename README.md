# JobLens Web Manager

前后端分离的 JobLens 分布式作业调度系统 Web 管理平台。

[English](README_EN.md)

## 系统架构

```
浏览器 → Vue 3 前端 → FastAPI 后端代理 → 注册中心 / JobLens Agent(采集器)
                                              │
                                          ETCD(配置存储)
```

后端通过 HTTP 调用外部注册中心获取服务列表，通过 ETCD 管理所有配置数据（模式、角色、规则、集群配置、服务属性），并通过各节点上的 JobLens Agent 执行作业管理与性能采集。

## 技术栈

### 后端
| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| HTTP 客户端 | httpx |
| 数据验证 | Pydantic + pydantic-settings |
| 存储 | ETCD (etcd3) |
| 规则引擎 | Lua (lupa) |

### 前端
| 组件 | 技术 |
|------|------|
| 框架 | Vue 3 + TypeScript |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| 图表 | ECharts |
| 代码编辑器 | Monaco Editor / CodeMirror |
| 国际化 | vue-i18n (中文 / 英文) |
| HTTP 客户端 | Axios |
| 构建工具 | Vite |

## 项目结构

```
joblens_web_manager/
├── backend/                          # Python 后端
│   ├── backend/
│   │   ├── main.py                   # FastAPI 应用入口
│   │   ├── config.py                 # 配置管理 (pydantic-settings)
│   │   ├── common/                   # 公共模块
│   │   │   ├── etcd_client.py        # ETCD 客户端管理
│   │   │   ├── db_init.py            # ETCD 初始化 (默认模式/角色)
│   │   │   └── logger.py             # 日志配置
│   │   ├── models/                   # Pydantic 数据模型
│   │   │   ├── service.py            # 服务模型
│   │   │   ├── job.py                # 作业模型
│   │   │   ├── metrics.py            # 指标模型
│   │   │   ├── role.py               # 角色/规则模型
│   │   │   ├── mode.py               # 模式模型
│   │   │   ├── cluster.py            # 集群模型
│   │   │   └── etcd_config.py        # ETCD 配置模型
│   │   ├── routers/                  # API 路由
│   │   │   ├── services.py           # 服务管理
│   │   │   ├── jobs.py               # 作业管理
│   │   │   ├── metrics.py            # 指标监控
│   │   │   ├── configs.py            # 配置管理 (旧版)
│   │   │   ├── modes.py              # 模式管理
│   │   │   ├── roles.py              # 角色管理
│   │   │   ├── rules.py              # 规则管理
│   │   │   └── clusters.py           # 集群管理
│   │   └── services/                 # 业务逻辑层
│   │       ├── registry_service.py   # 注册中心服务
│   │       ├── collector_service.py  # 采集器服务
│   │       └── lua_validator.py      # Lua 规则验证器
│   ├── requirements.txt              # 生产依赖
│   ├── requirements-test.txt         # 测试依赖
│   ├── pytest.ini                    # 测试配置
│   └── Dockerfile                    # 后端 Docker 镜像
├── frontend/                         # Vue 前端
│   ├── src/
│   │   ├── main.ts                   # 应用入口
│   │   ├── App.vue                   # 根组件 (布局/导航/安装弹窗)
│   │   ├── router/index.ts           # 路由配置
│   │   ├── api/                      # API 接口层
│   │   │   ├── config.ts             # Axios 实例 & 配置管理
│   │   │   ├── service.ts            # 服务管理
│   │   │   ├── job.ts                # 作业管理
│   │   │   ├── metrics.ts            # 指标监控
│   │   │   ├── cluster.ts            # 集群管理
│   │   │   ├── modes.ts              # 模式管理
│   │   │   ├── roles.ts              # 角色管理
│   │   │   └── rules.ts              # 规则管理
│   │   ├── views/                    # 页面视图
│   │   │   ├── Dashboard.vue         # 监控大盘
│   │   │   ├── ServiceList.vue       # 服务列表
│   │   │   ├── ServiceDetail.vue     # 服务详情
│   │   │   ├── JobManager.vue        # 作业管理
│   │   │   ├── ConfigManager.vue     # 配置管理 (模式 + YAML)
│   │   │   ├── RoleManager.vue       # 角色管理 (角色树 + 规则)
│   │   │   └── ClusterManager.vue    # 集群管理
│   │   ├── locales/                  # 国际化
│   │   │   ├── index.ts              # i18n 初始化
│   │   │   ├── zh-CN.ts              # 中文语言包
│   │   │   └── en.ts                 # 英文语言包
│   │   ├── components/               # 公共组件
│   │   │   └── TimezoneSelect.vue    # 时区选择器
│   │   └── utils/                    # 工具函数
│   │       ├── nodeExport.ts         # 节点导出
│   │       └── lua-highlight.ts      # Lua 语法高亮
│   ├── package.json
│   └── Dockerfile                    # 前端 Docker 镜像
├── LICENSE                           # Apache 2.0
└── ARCHITECTURE.md                   # 架构设计文档
```

## 功能特性

### 1. 监控大盘 (Dashboard)
- 服务状态统计：总数、健康、异常、活跃
- 集群标签分布展示
- 服务状态分布饼图

### 2. 服务管理
- 查看所有注册的服务节点（分页/搜索/筛选/排序）
- 按模式、角色、集群标签筛选服务
- 查看服务详情与健康状态（注册中心 + 采集器双重检测）
- 更新服务属性（模式/角色）
- 注销服务（带确认）
- 一键复制 JobLens Agent 安装命令
- 导出不健康节点列表

### 3. 作业管理
- 按服务节点查看作业列表（支持搜索/筛选）
- 创建普通作业（名称、命令、优先级、执行器、Cron、环境变量等）
- 创建 Condor 作业
- 删除作业（含实例清理选项）
- 查看作业详情

### 4. 配置管理（模式管理）
- 创建/编辑/删除模式
- 设置默认模式
- YAML 编辑器（基于 Monaco Editor，支持语法高亮和校验）
- 配置版本历史查看与回滚

### 5. 角色与规则管理
- 角色树结构，支持父子继承关系
- 创建/编辑/删除角色
- 规则管理（分页/搜索）
- 内嵌 Lua 代码编辑器（语法高亮 + 自动验证）
- 规则合并：子角色同 ID 规则覆盖父角色规则
- 角色生效规则预览（去重后）

### 6. 集群管理
- 左侧集群树（支持按名称搜索）
- 基本配置：别名、描述、启用状态
- 扩展必填配置：ES 地址/用户名/密码、节点端口、脚本路径等
- 自由扩展字段（JSON 格式）
- 集群精简视图（Scheme）

### 7. 国际化
- 支持中文（zh-CN）和英文（en）
- 自动检测浏览器语言，支持手动切换并持久化

## 安装和运行

### 前置依赖
- Python 3.10+
- Node.js 18+
- ETCD 3.x
- JobLens 注册中心（可选，部分功能依赖）

### 后端

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量（编辑 `backend/.env`）：
```env
REGISTRY_URL=http://localhost:8080
COLLECTOR_TIMEOUT=5.0
CACHE_TTL=30
ETCD_HOST=localhost
ETCD_PORT=2379
DEBUG=false
LOG_LEVEL=INFO
```

> 所有配置项见 [backend/backend/config.py](backend/backend/config.py)

3. 运行后端：
```bash
uvicorn backend.main:app --reload --port 8000
```

4. 访问 API 文档：
```
http://localhost:8000/docs
```

### 前端

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 配置环境变量（编辑 `frontend/.env`）：
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_REFRESH_INTERVAL=30000
VITE_DEFAULT_LANG=zh-CN
```

3. 运行前端：
```bash
npm run dev
```

4. 访问页面：
```
http://localhost:5173
```

### Docker 部署

前后端均提供 `Dockerfile`，可独立构建镜像。

后端构建：
```bash
cd backend && docker build -t joblens-webmanager-backend .
```

前端构建：
```bash
cd frontend && docker build -t joblens-webmanager-frontend .
```

## API 接口

### 服务管理 `/api/services`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/services` | 获取服务列表（分页/筛选/排序/搜索） |
| GET | `/api/services/count` | 服务总数 |
| GET | `/api/services/registry/health` | 注册中心健康状态 |
| GET | `/api/services/registry/stats` | 注册中心统计 |
| GET | `/api/services/cluster/tags` | 集群标签列表 |
| GET | `/api/services/{id}` | 服务详情 |
| GET | `/api/services/{id}/health` | 服务健康状态 |
| PUT | `/api/services/{id}/attributes` | 更新服务属性 |
| DELETE | `/api/services/{id}` | 注销服务 |

### 作业管理 `/api/jobs`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/jobs` | 获取作业列表 |
| GET | `/api/jobs/{job_id}` | 作业详情 |
| POST | `/api/jobs` | 创建作业 (condor/common) |
| DELETE | `/api/jobs/{job_id}` | 删除作业 |
| GET | `/api/jobs/{service_id}/count` | 作业数量 |

### 指标监控 `/api/metrics`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/metrics/services/{id}/collectors` | 采集器性能 |
| GET | `/api/metrics/services/{id}/writers` | Writer 性能 |
| GET | `/api/metrics/services/{id}/writers/{name}` | Writer 详情 |
| GET | `/api/metrics/services/{id}/all` | 全部指标 |
| GET | `/api/metrics/services/{id}/prometheus` | Prometheus 指标 |
| GET | `/api/metrics/registry` | 注册中心指标 |

### 模式管理 `/api/modes`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/modes` | 模式列表 |
| POST | `/api/modes` | 创建模式 |
| GET | `/api/modes/{name}` | 模式详情 |
| PUT | `/api/modes/{name}` | 更新模式 |
| DELETE | `/api/modes/{name}` | 删除模式 |
| GET | `/api/modes/{name}/config` | 获取模式配置 |
| PUT | `/api/modes/{name}/config` | 更新模式配置 |
| GET | `/api/modes/{name}/versions` | 版本历史 |
| GET | `/api/modes/{name}/version/{v}` | 指定版本配置 |
| POST | `/api/modes/{name}/rollback/{v}` | 回滚到指定版本 |

### 角色管理 `/api/roles`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/roles` | 角色列表 |
| POST | `/api/roles` | 创建角色 |
| GET | `/api/roles/{id}` | 角色详情 |
| PUT | `/api/roles/{id}` | 更新角色 |
| DELETE | `/api/roles/{id}` | 删除角色 |
| GET | `/api/roles/{id}/rules` | 角色规则（含继承） |
| GET | `/api/roles/{id}/rules/effective` | 生效规则（去重） |

### 规则管理 `/api/rules`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rules` | 规则列表（分页） |
| POST | `/api/rules` | 创建规则 |
| GET | `/api/rules/{id}` | 规则详情 |
| PUT | `/api/rules/{id}` | 更新规则 |
| DELETE | `/api/rules/{id}` | 删除规则 |

### 集群管理 `/api/clusters`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/clusters` | 集群列表 |
| GET | `/api/clusters/scheme` | 集群精简视图 |
| GET | `/api/clusters/{name}` | 集群详情 |
| PUT | `/api/clusters/{name}/config` | 更新集群配置 |

## 配置说明

### 后端配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `REGISTRY_URL` | `http://localhost:8080` | 注册中心地址 |
| `ETCD_HOST` | `localhost` | ETCD 主机 |
| `ETCD_PORT` | `2379` | ETCD 端口 |
| `ETCD_TIMEOUT` | `10` | ETCD 连接超时（秒） |
| `ETCD_CONFIG_PREFIX` | `/joblens/config/` | 模式/角色/规则存储前缀 |
| `ETCD_REGISTRY_PREFIX` | `/joblens_registry/services/` | 服务属性存储前缀 |
| `ETCD_CLUSTERS_INSTANCE_PREFIX` | `/joblens_registry/clusters/instance/` | 集群实例存储前缀 |
| `COLLECTOR_TIMEOUT` | `5.0` | 采集器请求超时（秒） |
| `CACHE_TTL` | `30` | 缓存 TTL（秒） |
| `DEBUG` | `false` | 调试模式 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 前端配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | 后端 API 地址 |
| `VITE_REFRESH_INTERVAL` | `30000` | 自动刷新间隔（毫秒） |
| `VITE_DEFAULT_LANG` | `zh-CN` | 默认语言 |

## 开发说明

### 后端

- 所有请求经过 FastAPI 代理，不直接暴露后端服务
- 使用 ETCD 作为唯一数据存储，无传统关系型数据库
- 启动时自动初始化默认模式和默认角色
- 服务属性（mode/role）从 ETCD 读取，服务状态从注册中心获取，两者合并返回
- Lua 规则通过 `lupa` 库在 Python 端验证语法和结构
- 配置变更自动保存历史版本，支持回滚

### 前端

- API 层集中在 `src/api/`，所有 HTTP 请求通过统一 Axios 实例
- 语言包文件 `src/locales/{zh-CN,en}.ts`，新增文本需同时更新两个文件
- 视图页面遵循 Element Plus 组件规范

### 测试

后端测试：
```bash
cd backend
pytest
```

前端测试：
```bash
cd frontend
npm run test:unit    # Vitest 单元测试
npm run test:e2e     # Playwright E2E 测试
npm run type-check   # TypeScript 类型检查
npm run lint         # ESLint 代码检查
```

## 故障排查

### 后端无法启动
- 确认 Python 3.10+ 已安装
- 确认所有依赖已安装：`pip install -r requirements.txt`
- 检查 ETCD 是否可连接，端口 2379 是否开放

### 前端无法连接后端
- 检查 `VITE_API_BASE_URL` 配置是否正确
- 确认后端服务正在运行
- 检查浏览器控制台是否有 CORS 错误

### 服务列表为空
- 检查 `REGISTRY_URL` 配置是否正确
- 确认注册中心服务正在运行且已注册服务节点
- 查看后端日志获取详细错误信息

## License

[Apache License 2.0](LICENSE)
