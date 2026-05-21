# AGENTS.md

## 项目概要

前后端分离的 JobLens 集群监控管理系统。前端 Vue 3 + Element Plus，后端 FastAPI 代理层，下游对接注册中心(8080)和采集器(7592)，ETCD 做配置存储。

## 目录与入口

```
backend/               # Python 后端 (FastAPI)
  backend/             # 真正的 Python 包 (嵌套结构!)
    main.py            # FastAPI app 工厂, 注册所有路由
    config.py          # pydantic-settings, 读 .env
    routers/           # 按资源拆分路由: services/jobs/metrics/configs/modes/roles/rules/clusters
    models/            # Pydantic 模型
    services/          # 业务逻辑: registry_service, collector_service, lua_validator
    common/            # ETCD 客户端, 日志, db_init
  tests/               # pytest, 测试路径在 pytest.ini 中配置
  Dockerfile           # 多阶段构建, Python 3.13-slim
  requirements.txt     # 生产依赖
  requirements-test.txt # 测试额外依赖
frontend/              # Vue 3 + Vite + TypeScript
  src/api/             # Axios API 客户端, 每个资源一个文件
  src/views/           # 页面组件
  src/router/index.ts  # 路由定义
  src/stores/          # Pinia stores
  src/components/      # 可复用组件
  Dockerfile           # 多阶段: node build → nginx:alpine-slim 服务
  nginx.conf           # 前端 nginx 配置
```

## 关键命令

```bash
# === 后端 ===
cd backend
source venv/bin/activate          # Python 虚拟环境必须先激活
uvicorn backend.main:app --reload --port 8000   # 注意 app 路径: backend.main:app (嵌套)
pytest                            # 从 backend/ 目录运行
pytest -m "not docker"            # 跳过需要 Docker 的 ETCD 集成测试
pytest tests/path/to/test.py -k "pattern"  # 运行单个测试
pytest -m unit                    # 只跑单元测试 (markers: unit, integration, api, service, slow, docker)

# === 前端 ===
cd frontend
npm run dev                       # Vite 开发服务器 (localhost:5173)
npm run build                     # 构建 (自动先 type-check)
npm run type-check                # vue-tsc --build (非 tsc!)
npm run lint                      # eslint --fix --cache
npm run format                    # prettier (semi=false, singleQuote, printWidth=100)
npm run test                      # vitest run
npm run test -- -t "pattern"      # 运行匹配的 vitest 测试
```

## 运行测试的要点

- **后端测试必须从 `backend/` 目录运行**：`conftest.py` 通过 `sys.path.insert` 添加父目录，在别处运行会导入失败。
- **后端 autouse fixture 覆盖环境变量**：`override_settings` 把 ETCD_HOST→localhost, REGISTRY_URL→mock-registry, 避免依赖真实服务。
- **标记 `docker` 的测试**需要 Docker 守护进程和 `docker-py` 包，跳过用 `-m "not docker"`。
- **前端测试用 vitest + jsdom**：配置在 `vite.config.ts` 的 `test` 字段，测试文件匹配 `src/**/*.test.ts`。

## 重要约束与坑

1. **嵌套包结构**：Python 包在 `backend/backend/`，导入用 `from backend.xxx import yyy`，uvicorn 入口是 `backend.main:app`。切忌把 `backend/main.py` 当入口（那个不存在）。
2. **ETCD 是硬依赖**：应用启动时 `lifespan` 事件调用 `initialize_etcd()` 连接 ETCD 并创建默认模式和角色；ETCD 不可用时启动直接失败。
3. **protobuf 版本锁定**：`requirements.txt` 要求 `protobuf<3.20`，这是 etcd3 客户端的兼容性约束，不要升级。
4. **`.env` 文件有 gitignore 规则**：`*.env` 在 `.gitignore` 中，本地的 `.env` 不会提交。后端 `.env` 配置 ETCD 连接、注册中心 URL 等；前端 `.env` 配置 `VITE_API_BASE_URL` 等。
5. **后端无 lint/format 脚本**：Black/flake8/isort 在 `requirements-test.txt` 中，但没有预配置的 npm 风格脚本，需要手动运行。
6. **前端 type-check 用 vue-tsc**：不能用 `tsc`，因为 `.vue` 文件的类型需要 `vue-tsc` 才能解析。
7. **Lua 规则验证依赖 lupa**：lupa>=2.0 需要系统安装 Lua，编辑规则相关代码时注意。
8. **Node 版本要求**：`^20.19.0 || >=22.12.0`（见 `frontend/package.json` 的 engines 字段）。

## 代码风格约定

- 后端：APIRouter 按资源拆分，在 `main.py` 中统一 `include_router`，所有 API 前缀 `/api`。路由共 8 个：services, jobs, metrics, configs, modes, roles, rules, clusters。
- 前端：Composition API (`<script setup lang="ts">`)，ESLint flat config，`@/` 别名指向 `src/`。
- 新功能流程：后端模型 → 路由 → main.py 注册；前端 API 客户端 → 视图 → router → App.vue 导航。
- ETCD 键名使用 `/joblens/config/{资源}/{id}` 格式；注册中心数据在 `/joblens_registry/` 前缀下。

## CI/CD

- GitLab CI（`.gitlab-ci.yml`）：两个阶段 build → push，分别构建和推送前后端 Docker 镜像到私有注册表。
- 后端 Dockerfile：多阶段构建（builder→runner），Python 3.13-slim，端口 8000，有健康检查。
- 前端 Dockerfile：多阶段构建（node build→nginx:alpine-slim），端口 80，启动时通过 sed 替换运行时配置占位符。
