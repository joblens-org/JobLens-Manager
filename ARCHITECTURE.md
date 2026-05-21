# JobLens Web Manager 架构与功能说明

## 项目概览

**JobLens Web Manager** 是一个前后端分离的监控管理Web系统，用于管理和监控JobLens服务集群。系统通过Python后端代理与注册中心（8080端口）和采集器（7592端口）通信，提供统一的管理界面。

### 主要用途
- 服务节点注册与健康状态监控
- 作业管理和调度
- 配置管理和版本控制
- 角色和规则管理（新增功能）
- 模式和筛选管理（新增功能）

### 技术栈
- **后端**: FastAPI + Python + ETCD存储
- **前端**: Vue 3 + TypeScript + Element Plus UI
- **存储**: ETCD（配置、模式、角色、规则存储）
- **通信**: HTTP RESTful API + WebSocket（可选）

### 项目结构
```
joblens_web_manager/
├── ARCHITECTURE.md           # 本文档（架构说明）
├── README.md                 # 项目基础文档
├── backend/                  # Python后端
│   ├── backend/
│   │   ├── main.py          # FastAPI主应用（包含所有路由注册）
│   │   ├── config.py        # 配置类（ETCD连接、注册中心URL等）
│   │   ├── models/          # Pydantic数据模型
│   │   │   ├── __init__.py
│   │   │   ├── etcd_config.py  # ETCD配置相关模型
│   │   │   ├── job.py       # 作业模型
│   │   │   ├── metrics.py   # 监控指标模型
│   │   │   ├── mode.py      # 模式模型（新增）
│   │   │   ├── role.py      # 角色和规则模型（新增）
│   │   │   └── service.py   # 服务模型（新增mode和role_id字段）
│   │   ├── routers/         # API路由
│   │   │   ├── __init__.py
│   │   │   ├── configs.py   # 配置管理路由（重构支持模式）
│   │   │   ├── jobs.py      # 作业管理路由
│   │   │   ├── metrics.py   # 监控指标路由
│   │   │   ├── modes.py     # 模式管理路由（新增）
│   │   │   ├── roles.py     # 角色管理路由（新增）
│   │   │   └── services.py  # 服务管理路由（增强筛选功能）
│   │   └── services/        # 业务逻辑服务
│   │       ├── __init__.py
│   │       ├── collector_service.py  # 采集器服务
│   │       └── registry_service.py   # 注册中心服务
│   ├── requirements.txt     # Python依赖
│   ├── .env                # 环境变量配置
│   └── venv/               # Python虚拟环境
├── frontend/               # Vue前端
│   ├── src/
│   │   ├── api/           # API客户端
│   │   │   ├── config.ts  # API配置和基础客户端
│   │   │   ├── index.ts   # API导出
│   │   │   ├── job.ts     # 作业API
│   │   │   ├── metrics.ts # 监控API
│   │   │   ├── modes.ts   # 模式API（新增）
│   │   │   ├── roles.ts   # 角色API（新增）
│   │   │   └── service.ts # 服务API（增强筛选）
│   │   ├── assets/        # 静态资源
│   │   ├── components/    # 公共组件
│   │   ├── router/        # 路由配置
│   │   │   └── index.ts   # Vue路由定义（包含角色管理路由）
│   │   ├── stores/        # 状态管理
│   │   ├── views/         # 页面视图
│   │   │   ├── AboutView.vue
│   │   │   ├── ConfigManager.vue   # 配置管理（重构支持多模式）
│   │   │   ├── Dashboard.vue       # 监控大盘
│   │   │   ├── HomeView.vue
│   │   │   ├── JobManager.vue      # 作业管理
│   │   │   ├── RoleManager.vue     # 角色管理（新增）
│   │   │   ├── ServiceDetail.vue   # 服务详情（增强显示模式角色）
│   │   │   └── ServiceList.vue     # 服务列表（增强筛选功能）
│   │   ├── App.vue        # 主应用组件（包含导航菜单）
│   │   └── main.ts        # 应用入口
│   ├── package.json       # 前端依赖
│   ├── .env              # 前端环境变量
│   └── public/           # 公共文件
└── app.py                # JobLens采集器（外部服务）
```

## 功能模块

### 1. 监控大盘 (Dashboard)
- 服务状态统计（总数、健康、异常、活跃）
- 服务状态分布图表（使用ECharts）
- 最近服务列表
- 注册中心健康状态监控

### 2. 服务管理
#### 服务列表 (ServiceList.vue)
- 查看所有注册的服务节点
- 按模式筛选服务（新增）
- 按角色筛选服务（新增）
- 仅显示健康服务筛选
- 服务详情查看和注销功能
- 显示服务模式和角色信息

#### 服务详情 (ServiceDetail.vue)
- 服务基本信息展示
- 服务健康状态检查（注册中心+采集器）
- 模式和角色信息显示（新增）
- 关联的作业列表
- 性能指标查看

### 3. 作业管理 (JobManager.vue)
- 查看跨所有服务的作业列表
- 添加新作业（支持普通作业和Condor作业）
- 删除作业功能
- 查看作业详细信息
- 作业数量统计

### 4. 配置管理 (ConfigManager.vue) - 重构
**原功能：**
- Develop/Test环境配置管理
- YAML配置编辑
- 配置版本历史

**新增功能：**
- 动态模式管理系统（替代静态环境概念）
- 多模式配置编辑（支持创建、编辑、删除模式）
- 模式间的配置复制和继承
- 模式配置版本管理

### 5. 角色与规则管理 (RoleManager.vue) - 新增
**角色管理：**
- 角色树形结构展示（支持继承关系）
- 角色创建、编辑、删除
- 角色继承机制（引用继承，修改时Copy-on-Write）
- 角色关联服务数量统计

**规则管理：**
- Lua规则编辑器（代码高亮、语法检查）
- 规则继承和覆盖机制（Copy-on-Write）
- 规则版本管理
- 规则与角色关联管理

### 6. 筛选功能 - 增强
- 服务列表按模式筛选（下拉选择）
- 服务列表按角色筛选（下拉选择）
- 筛选条件组合查询
- 筛选选项动态加载（从API获取模式列表和角色列表）

## 技术架构

### 后端架构 (FastAPI)
```
FastAPI应用 (backend/main.py)
├── CORS中间件配置
├── 路由注册
│   ├── /api/services/*    (services.router)
│   ├── /api/jobs/*        (jobs.router)
│   ├── /api/metrics/*     (metrics.router)
│   ├── /api/configs/*     (configs.router)
│   ├── /api/modes/*       (modes.router)     ← 新增
│   └── /api/roles/*       (roles.router)     ← 新增
├── ETCD客户端连接池
└── 业务服务层
    ├── RegistryService (注册中心通信)
    └── CollectorService (采集器通信)
```

### 前端架构 (Vue 3)
```
Vue应用 (frontend/src/main.ts)
├── 路由系统 (router/index.ts)
├── 全局状态管理 (stores/)
├── API客户端层 (api/)
├── 页面组件 (views/)
├── 公共组件 (components/)
└── Element Plus UI组件库
```

### 数据存储架构
```
ETCD键值存储
├── /services/                    # 服务注册信息
├── /jobs/                       # 作业信息
├── /configs/{mode}/             # 模式配置（新增）
│   ├── /config.yaml            # 当前配置
│   └── /versions/{timestamp}/  # 历史版本
├── /modes/                      # 模式定义（新增）
├── /roles/                      # 角色定义（新增）
└── /rules/                      # 规则定义（新增）
```

### 前后端通信
- **协议**: HTTP RESTful API
- **认证**: 暂无（可根据需要添加）
- **数据格式**: JSON
- **错误处理**: 标准化错误响应格式
- **CORS**: 已配置允许所有源（开发环境）

## 数据模型

### 服务模型 (ServiceInfo)
```python
class ServiceInfo(BaseModel):
    service_id: str          # 服务ID
    host: str               # 主机地址
    port: int               # 端口
    name: str               # 服务名称
    version: str            # 版本号
    base_url: str           # 基础URL
    status: str             # 状态（healthy/unhealthy）
    registered_at: datetime # 注册时间
    last_heartbeat: Optional[datetime]  # 最后心跳
    mode: Optional[str]     # 关联的模式名称（新增）
    role_id: Optional[str]  # 关联的角色ID（新增）
    metadata: Optional[dict] # 元数据
```

### 模式模型 (ModeInfo)
```python
class ModeInfo(BaseModel):
    name: str               # 模式名称（唯一标识）
    description: Optional[str]  # 模式描述
    created_at: datetime    # 创建时间
    updated_at: datetime    # 更新时间
    is_default: bool        # 是否为默认模式
    config_count: int       # 关联的配置数量
```

### 角色模型 (RoleInfo)
```python
class RoleInfo(BaseModel):
    role_id: str            # 角色ID（UUID）
    name: str               # 角色名称（唯一）
    description: Optional[str]  # 角色描述
    parent_role_id: Optional[str]  # 父角色ID（继承）
    rule_ids: List[str]     # 关联的规则ID列表
    created_at: datetime    # 创建时间
    updated_at: datetime    # 更新时间
    service_count: int      # 使用此角色的服务数量
    metadata: Optional[Dict[str, Any]]  # 角色元数据
```

### 规则模型 (RuleInfo)
```python
class RuleInfo(BaseModel):
    rule_id: str            # 规则ID（UUID）
    name: str               # 规则名称
    lua_content: str        # Lua规则内容
    created_at: datetime    # 创建时间
    updated_at: datetime    # 更新时间
    version: int            # 版本号
    parent_rule_id: Optional[str]  # 父规则ID（继承）
    is_override: bool       # 是否为覆盖规则（Copy-on-Write）
    metadata: Optional[Dict[str, Any]]  # 规则元数据
```

## API接口

### 模式管理接口 (/api/modes)
| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| GET | `/modes` | 获取模式列表 | 支持分页参数 |
| POST | `/modes` | 创建新模式 | |
| GET | `/modes/{mode_name}` | 获取模式详情 | |
| PUT | `/modes/{mode_name}` | 更新模式信息 | |
| DELETE | `/modes/{mode_name}` | 删除模式 | |
| GET | `/modes/{mode_name}/config` | 获取模式配置 | |
| PUT | `/modes/{mode_name}/config` | 更新模式配置 | |
| GET | `/modes/{mode_name}/versions` | 获取配置版本历史 | |

### 角色管理接口 (/api/roles)
| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| GET | `/roles` | 获取角色列表 | 支持分页参数 |
| POST | `/roles` | 创建新角色 | |
| GET | `/roles/{role_id}` | 获取角色详情 | 包含规则信息 |
| PUT | `/roles/{role_id}` | 更新角色信息 | |
| DELETE | `/roles/{role_id}` | 删除角色 | |
| POST | `/roles/{role_id}/rules` | 为角色添加规则 | |
| PUT | `/roles/{role_id}/rules/{rule_id}` | 更新规则 | |
| DELETE | `/roles/{role_id}/rules/{rule_id}` | 删除规则 | |
| GET | `/roles/{role_id}/inheritance` | 获取角色继承链 | |

### 服务管理接口 (/api/services) - 增强
| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| GET | `/services` | 获取服务列表 | 新增mode和role_id筛选参数 |
| GET | `/services/filter-options` | 获取筛选选项 | 新增接口，返回模式列表和角色列表 |
| PUT | `/services/{service_id}/attributes` | 更新服务属性 | 新增接口，更新模式和角色 |

### 配置管理接口 (/api/configs) - 重构
- 所有接口从`/{environment}`参数改为`/{mode}`参数
- 支持动态模式配置管理

## 前端组件结构

### 路由配置 (router/index.ts)
```typescript
const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/services', name: 'services', component: ServiceList },
  { path: '/services/:id', name: 'service-detail', component: ServiceDetail },
  { path: '/jobs', name: 'jobs', component: JobManager },
  { path: '/configs', name: 'configs', component: ConfigManager },
  { path: '/roles', name: 'roles', component: RoleManager }, // 新增
]
```

### 导航菜单 (App.vue)
```javascript
const menuItems = [
  { path: '/', icon: 'Monitor', label: '监控大盘' },
  { path: '/services', icon: 'Service', label: '服务列表' },
  { path: '/jobs', icon: 'Document', label: '作业管理' },
  { path: '/configs', icon: 'Setting', label: '配置管理' },
  { path: '/roles', icon: 'User', label: '角色管理' }, // 新增
]
```

### 关键组件功能

#### RoleManager.vue
- **角色树组件**: 展示角色继承关系的树形结构
- **规则编辑器**: 集成CodeMirror的Lua代码编辑器
- **继承管理**: 处理角色和规则的继承关系
- **Copy-on-Write**: 修改继承规则时自动创建副本

#### ConfigManager.vue (重构)
- **模式选择器**: 动态加载模式列表，支持模式创建
- **多标签页**: 每个模式独立标签页，支持并行编辑
- **配置版本**: 每个模式的配置版本历史独立管理

#### ServiceList.vue (增强)
- **筛选控件**: 模式和角色下拉筛选组件
- **动态选项**: 从API加载筛选选项
- **表格列**: 新增模式和角色显示列

## 新增功能详细说明

### 1. 模式管理系统
**设计目标**: 替代原有的静态环境概念（Develop/Test），实现动态模式管理

**核心特性**:
- **动态创建**: 可随时创建新的模式，无需修改代码
- **配置独立**: 每个模式有独立的配置存储
- **版本管理**: 每个模式的配置有独立版本历史
- **默认模式**: 支持设置默认模式

**实现机制**:
- 后端: `backend/models/mode.py` 定义数据模型
- 后端: `backend/routers/modes.py` 提供CRUD API
- 前端: `frontend/src/api/modes.ts` API客户端
- 前端: `frontend/src/views/ConfigManager.vue` 集成模式选择

**ETCD存储结构**:
```
/modes/{mode_name}/info         # 模式元数据
/modes/{mode_name}/config       # 当前配置
/modes/{mode_name}/versions/{timestamp}  # 历史版本
```

### 2. 角色和规则管理系统
**设计目标**: 实现灵活的角色权限和规则管理，支持继承机制

**核心特性**:
- **角色继承**: 角色可继承父角色的所有规则
- **Copy-on-Write**: 修改继承规则时自动创建副本，不影响父角色
- **Lua规则**: 使用Lua脚本定义业务规则
- **规则版本**: 规则修改时创建新版本

**继承机制**:
1. **引用继承**: 角色继承时，规则通过引用共享
2. **修改检测**: 当修改继承的规则时，触发Copy-on-Write
3. **副本创建**: 创建规则副本，更新角色引用关系
4. **版本管理**: 新规则作为独立版本管理

**实现机制**:
- 后端: `backend/models/role.py` 定义角色和规则模型
- 后端: `backend/routers/roles.py` 提供CRUD API
- 前端: `frontend/src/api/roles.ts` API客户端
- 前端: `frontend/src/views/RoleManager.vue` 完整管理界面

**ETCD存储结构**:
```
/roles/{role_id}/info          # 角色元数据
/roles/{role_id}/rules         # 规则ID列表
/rules/{rule_id}/info          # 规则元数据
/rules/{rule_id}/content       # Lua规则内容
/rules/{rule_id}/versions/{version}  # 规则版本
```

### 3. 服务筛选功能
**设计目标**: 在服务列表页面提供灵活的筛选能力

**核心特性**:
- **模式筛选**: 按关联的模式筛选服务
- **角色筛选**: 按关联的角色筛选服务
- **组合筛选**: 支持模式和角色组合筛选
- **动态选项**: 筛选选项从API实时获取

**实现机制**:
- 后端: `backend/routers/services.py` 扩展`list_services`接口
- 后端: 新增`get_filter_options`接口
- 前端: `frontend/src/api/service.ts` 更新API客户端
- 前端: `frontend/src/views/ServiceList.vue` 添加筛选控件

**API变化**:
- `GET /api/services` 新增`mode`和`role_id`查询参数
- `GET /api/services/filter-options` 新增接口，返回可用筛选选项
- `PUT /api/services/{id}/attributes` 新增接口，更新服务属性

## 部署和运行

### 后端部署
1. **环境准备**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **配置环境变量** (backend/.env):
   ```env
   REGISTRY_URL=http://localhost:8080
   COLLECTOR_TIMEOUT=5.0
   CACHE_TTL=30
   ETCD_HOST=localhost
   ETCD_PORT=2379
   ```

3. **运行服务**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

4. **API文档**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### 前端部署
1. **环境准备**:
   ```bash
   cd frontend
   npm install
   ```

2. **配置环境变量** (frontend/.env):
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   VITE_REFRESH_INTERVAL=30000
   ```

3. **开发模式**:
   ```bash
   npm run dev
   ```

4. **生产构建**:
   ```bash
   npm run build
   ```

### 数据迁移（现有环境转模式）
现有环境（Develop/Test）需要迁移到新模式系统：

1. **自动迁移脚本** (待实现):
   ```python
   # 将现有Develop环境转换为"develop"模式
   # 将现有Test环境转换为"test"模式
   # 迁移配置历史版本
   ```

2. **手动迁移步骤**:
   - 创建"develop"和"test"模式
   - 复制现有配置到对应模式
   - 更新服务关联的模式字段

## 开发指南

### 添加新功能
1. **后端开发流程**:
   - 在`backend/models/`添加数据模型
   - 在`backend/routers/`添加API路由
   - 在`backend/main.py`注册路由
   - 更新`backend/requirements.txt`（如需新依赖）

2. **前端开发流程**:
   - 在`frontend/src/api/`添加API客户端
   - 在`frontend/src/views/`添加页面组件
   - 在`frontend/src/router/index.ts`添加路由
   - 在`frontend/src/App.vue`添加导航菜单（如需）

### 测试
1. **后端测试**:
   ```bash
   cd backend
   pytest
   ```

2. **前端测试**:
   - 组件单元测试（待实现）
   - API集成测试（待实现）

### 代码规范
- **Python**: 使用Black格式化，遵循PEP 8
- **TypeScript**: 使用ESLint和Prettier
- **Vue**: 使用Vue 3组合式API
- **提交信息**: 遵循Conventional Commits

## 故障排除

### 常见问题
1. **后端无法连接ETCD**:
   - 检查ETCD服务状态
   - 验证`ETCD_HOST`和`ETCD_PORT`配置
   - 检查网络连接和防火墙

2. **前端无法连接后端**:
   - 检查`VITE_API_BASE_URL`配置
   - 验证后端服务是否运行
   - 检查浏览器控制台错误信息

3. **模式/角色API返回404**:
   - 检查后端路由是否正确注册
   - 验证API路径前缀（`/api/modes/`, `/api/roles/`）
   - 检查后端日志中的导入错误

4. **筛选功能不生效**:
   - 检查服务数据是否包含mode和role_id字段
   - 验证筛选参数是否正确传递到API
   - 检查`get_filter_options`接口返回数据

### 调试建议
1. **后端调试**:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   - 访问`http://localhost:8000/docs`测试API
   - 查看控制台日志输出

2. **前端调试**:
   - 使用Vue DevTools检查组件状态
   - 浏览器开发者工具查看网络请求
   - 控制台查看错误和警告

## 扩展计划

### 短期改进
1. **数据迁移脚本**: 自动化现有环境到模式的迁移
2. **角色权限控制**: 基于角色的UI权限控制
3. **规则语法验证**: Lua语法检查和验证
4. **批量操作**: 服务的批量模式和角色分配

### 长期规划
1. **审计日志**: 记录所有配置和规则变更
2. **通知系统**: 配置变更和服务状态告警
3. **多租户支持**: 多团队/项目隔离
4. **API密钥管理**: 安全的API访问控制

---

**文档版本**: 1.0  
**最后更新**: 2026-01-11  
**维护者**: JobLens开发团队