# JobLens Web Manager

前后端分离的 JobLens 分布式作业调度系统 Web 管理平台。

[English](README.md)

## 系统架构

```
浏览器 → Vue 3 前端 → FastAPI 后端代理 → 注册中心 / JobLens Agent(采集器)
                                              │
                                          ETCD(配置存储)
```

后端通过 HTTP 调用外部注册中心获取服务列表，通过 ETCD 管理所有配置数据（模式、角色、规则、集群配置、服务属性），并通过各节点上的 JobLens Agent 执行作业管理与性能采集。

## 功能特性

- **监控大盘** — 服务健康概览、集群标签分布、状态图表
- **服务管理** — 查看、筛选、编辑、注销服务节点；通过注册中心和采集器双重健康检测
- **作业管理** — 创建、查看和删除作业（标准作业和 Condor）
- **配置管理** — 动态模式管理，支持 YAML 编辑和版本历史
- **角色与规则管理** — 层级角色树，Lua 规则编辑器，支持继承
- **集群管理** — 配置集群属性、别名和扩展字段
- **国际化** — 自动检测浏览器语言，支持中文和英文
- **认证** — JWT 登录，支持 IP 白名单绕过

## 快速开始

### 前置依赖
- Python 3.10+
- Node.js 20+（见 `frontend/package.json` 中的 `engines`）
- ETCD 3.x
- JobLens 注册中心（可选，部分功能依赖）

### 后端

```bash
cd backend
pip install -r requirements.txt

# 配置：编辑 backend/.env
uvicorn backend.main:app --reload --port 8000
```

API 文档：http://localhost:8000/docs

### 前端

```bash
cd frontend
npm install

# 配置：编辑 frontend/.env
npm run dev
```

访问：http://localhost:5173

### Docker

```bash
cd backend && docker build -t joblens-webmanager-backend .
cd frontend && docker build -t joblens-webmanager-frontend .
```

## 项目结构

```
joblens_web_manager/
├── backend/           # Python + FastAPI + ETCD
│   ├── backend/       # 应用代码
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # Vue 3 + TypeScript + Vite
│   ├── src/           # 应用代码
│   ├── package.json
│   └── Dockerfile
├── doc/               # 文档
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── CONFIGURATION.md
│   └── DEVELOPMENT.md
├── README.md
├── README_CN.md
└── LICENSE
```

## 文档

| 文档 | 说明 |
|------|------|
| [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) | 完整架构概述、数据模型和组件详情 |
| [doc/API.md](doc/API.md) | 完整 API 接口参考 |
| [doc/CONFIGURATION.md](doc/CONFIGURATION.md) | 前后端配置参数 |
| [doc/DEVELOPMENT.md](doc/DEVELOPMENT.md) | 开发指南、测试和故障排查 |

> 以上文档为英文。中文版本保留了完整的中文参考内容，但详细文档请查看英文版。

## License

[Apache License 2.0](LICENSE)
