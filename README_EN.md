# JobLens Web Manager

A web management platform for the JobLens distributed job scheduling system, built with a decoupled frontend-backend architecture.

[中文](README.md)

## Architecture

```
Browser → Vue 3 Frontend → FastAPI Backend Proxy → Registry / JobLens Agent (Collector)
                                                      │
                                                  ETCD (Config Storage)
```

The backend communicates with the external registry service via HTTP to retrieve service listings, uses ETCD for all configuration data (modes, roles, rules, cluster configs, service attributes), and interacts with JobLens agents on each node for job management and performance collection.

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI + Uvicorn |
| HTTP Client | httpx |
| Data Validation | Pydantic + pydantic-settings |
| Storage | ETCD (etcd3) |
| Rule Engine | Lua (lupa) |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Vue 3 + TypeScript |
| UI Library | Element Plus |
| State Management | Pinia |
| Charts | ECharts |
| Code Editor | Monaco Editor / CodeMirror |
| Internationalization | vue-i18n (Chinese / English) |
| HTTP Client | Axios |
| Build Tool | Vite |

## Project Structure

```
joblens_web_manager/
├── backend/                          # Python Backend
│   ├── backend/
│   │   ├── main.py                   # FastAPI Application Entry
│   │   ├── config.py                 # Configuration (pydantic-settings)
│   │   ├── common/                   # Common Modules
│   │   │   ├── etcd_client.py        # ETCD Client Manager
│   │   │   ├── db_init.py            # ETCD Initialization (default mode/role)
│   │   │   └── logger.py             # Logging Configuration
│   │   ├── models/                   # Pydantic Data Models
│   │   │   ├── service.py            # Service Models
│   │   │   ├── job.py                # Job Models
│   │   │   ├── metrics.py            # Metrics Models
│   │   │   ├── role.py               # Role & Rule Models
│   │   │   ├── mode.py               # Mode Models
│   │   │   ├── cluster.py            # Cluster Models
│   │   │   └── etcd_config.py        # ETCD Config Models
│   │   ├── routers/                  # API Routes
│   │   │   ├── services.py           # Service Management
│   │   │   ├── jobs.py               # Job Management
│   │   │   ├── metrics.py            # Metrics Monitoring
│   │   │   ├── configs.py            # Config Management (legacy)
│   │   │   ├── modes.py              # Mode Management
│   │   │   ├── roles.py              # Role Management
│   │   │   ├── rules.py              # Rule Management
│   │   │   └── clusters.py           # Cluster Management
│   │   └── services/                 # Business Logic Layer
│   │       ├── registry_service.py   # Registry Service
│   │       ├── collector_service.py  # Collector Service
│   │       └── lua_validator.py      # Lua Rule Validator
│   ├── requirements.txt              # Production Dependencies
│   ├── requirements-test.txt         # Test Dependencies
│   ├── pytest.ini                    # Test Configuration
│   └── Dockerfile                    # Backend Docker Image
├── frontend/                         # Vue Frontend
│   ├── src/
│   │   ├── main.ts                   # Application Entry
│   │   ├── App.vue                   # Root Component (layout/nav/install dialog)
│   │   ├── router/index.ts           # Route Configuration
│   │   ├── api/                      # API Layer
│   │   │   ├── config.ts             # Axios Instance & Config API
│   │   │   ├── service.ts            # Service API
│   │   │   ├── job.ts                # Job API
│   │   │   ├── metrics.ts            # Metrics API
│   │   │   ├── cluster.ts            # Cluster API
│   │   │   ├── modes.ts              # Modes API
│   │   │   ├── roles.ts              # Roles API
│   │   │   └── rules.ts              # Rules API
│   │   ├── views/                    # Page Views
│   │   │   ├── Dashboard.vue         # Dashboard
│   │   │   ├── ServiceList.vue       # Service List
│   │   │   ├── ServiceDetail.vue     # Service Detail
│   │   │   ├── JobManager.vue        # Job Manager
│   │   │   ├── ConfigManager.vue     # Config Manager (modes + YAML)
│   │   │   ├── RoleManager.vue       # Role Manager (role tree + rules)
│   │   │   └── ClusterManager.vue    # Cluster Manager
│   │   ├── locales/                  # Internationalization
│   │   │   ├── index.ts              # i18n Initialization
│   │   │   ├── zh-CN.ts              # Chinese Language Pack
│   │   │   └── en.ts                 # English Language Pack
│   │   ├── components/               # Shared Components
│   │   │   └── TimezoneSelect.vue    # Timezone Picker
│   │   └── utils/                    # Utility Functions
│   │       ├── nodeExport.ts         # Node Export
│   │       └── lua-highlight.ts      # Lua Syntax Highlight
│   ├── package.json
│   └── Dockerfile                    # Frontend Docker Image
├── LICENSE                           # Apache 2.0
└── ARCHITECTURE.md                   # Architecture Design Document
```

## Features

### 1. Dashboard
- Service health overview: total, healthy, unhealthy, active
- Cluster tag distribution
- Service status distribution chart

### 2. Service Management
- View all registered service nodes (paginated, searchable, filterable, sortable)
- Filter services by mode, role, and cluster tags
- View service details and health status (dual-check: registry + collector)
- Update service attributes (mode/role)
- Deregister services (with confirmation)
- One-click copy JobLens Agent installation command
- Export unhealthy node list

### 3. Job Management
- View jobs per service node (searchable and filterable)
- Create standard jobs (name, command, priority, executor, cron, environment variables, etc.)
- Create Condor jobs
- Delete jobs (with instance cleanup option)
- View job details

### 4. Configuration Management (Mode Management)
- Create/edit/delete modes
- Set default mode
- YAML editor (based on Monaco Editor, with syntax highlighting and validation)
- View and rollback configuration version history

### 5. Role and Rule Management
- Role tree structure with parent-child inheritance
- Create/edit/delete roles
- Rule management (paginated, searchable)
- Built-in Lua code editor (syntax highlighting + automatic validation)
- Rule merging: child role rules with same ID override parent role rules
- Effective rules preview (deduplicated)

### 6. Cluster Management
- Left-side cluster tree (searchable by name)
- Basic configuration: alias, description, enabled status
- Required extension config: ES address/username/password, node port, script path, etc.
- Free-form extension fields (JSON format)
- Cluster condensed view (Scheme)

### 7. Internationalization
- Chinese (zh-CN) and English (en)
- Auto-detects browser language, supports manual switching with persistence

## Installation and Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- ETCD 3.x
- JobLens Registry (optional, some features depend on it)

### Backend

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment variables (edit `backend/.env`):
```env
REGISTRY_URL=http://localhost:8080
COLLECTOR_TIMEOUT=5.0
CACHE_TTL=30
ETCD_HOST=localhost
ETCD_PORT=2379
DEBUG=false
LOG_LEVEL=INFO
```

> See [backend/backend/config.py](backend/backend/config.py) for all configuration options

3. Run backend:
```bash
uvicorn backend.main:app --reload --port 8000
```

4. Access API docs:
```
http://localhost:8000/docs
```

### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables (edit `frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_REFRESH_INTERVAL=30000
VITE_DEFAULT_LANG=zh-CN
```

3. Run frontend:
```bash
npm run dev
```

4. Access application:
```
http://localhost:5173
```

### Docker Deployment

Both frontend and backend provide `Dockerfile` for independent image builds.

Build backend:
```bash
cd backend && docker build -t joblens-webmanager-backend .
```

Build frontend:
```bash
cd frontend && docker build -t joblens-webmanager-frontend .
```

## API Endpoints

### Service Management `/api/services`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/services` | Service list (paginated, filtered, sorted, searched) |
| GET | `/api/services/count` | Total service count |
| GET | `/api/services/registry/health` | Registry health status |
| GET | `/api/services/registry/stats` | Registry statistics |
| GET | `/api/services/cluster/tags` | Cluster tag list |
| GET | `/api/services/{id}` | Service details |
| GET | `/api/services/{id}/health` | Service health status |
| PUT | `/api/services/{id}/attributes` | Update service attributes |
| DELETE | `/api/services/{id}` | Deregister service |

### Job Management `/api/jobs`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs` | Job list |
| GET | `/api/jobs/{job_id}` | Job details |
| POST | `/api/jobs` | Create job (condor/common) |
| DELETE | `/api/jobs/{job_id}` | Delete job |
| GET | `/api/jobs/{service_id}/count` | Job count |

### Metrics `/api/metrics`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metrics/services/{id}/collectors` | Collector performance |
| GET | `/api/metrics/services/{id}/writers` | Writer performance |
| GET | `/api/metrics/services/{id}/writers/{name}` | Writer details |
| GET | `/api/metrics/services/{id}/all` | All metrics |
| GET | `/api/metrics/services/{id}/prometheus` | Prometheus metrics |
| GET | `/api/metrics/registry` | Registry metrics |

### Mode Management `/api/modes`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/modes` | Mode list |
| POST | `/api/modes` | Create mode |
| GET | `/api/modes/{name}` | Mode details |
| PUT | `/api/modes/{name}` | Update mode |
| DELETE | `/api/modes/{name}` | Delete mode |
| GET | `/api/modes/{name}/config` | Get mode config |
| PUT | `/api/modes/{name}/config` | Update mode config |
| GET | `/api/modes/{name}/versions` | Version history |
| GET | `/api/modes/{name}/version/{v}` | Specific version config |
| POST | `/api/modes/{name}/rollback/{v}` | Rollback to version |

### Role Management `/api/roles`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/roles` | Role list |
| POST | `/api/roles` | Create role |
| GET | `/api/roles/{id}` | Role details |
| PUT | `/api/roles/{id}` | Update role |
| DELETE | `/api/roles/{id}` | Delete role |
| GET | `/api/roles/{id}/rules` | Role rules (with inheritance) |
| GET | `/api/roles/{id}/rules/effective` | Effective rules (deduplicated) |

### Rule Management `/api/rules`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/rules` | Rule list (paginated) |
| POST | `/api/rules` | Create rule |
| GET | `/api/rules/{id}` | Rule details |
| PUT | `/api/rules/{id}` | Update rule |
| DELETE | `/api/rules/{id}` | Delete rule |

### Cluster Management `/api/clusters`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/clusters` | Cluster list |
| GET | `/api/clusters/scheme` | Cluster condensed view |
| GET | `/api/clusters/{name}` | Cluster details |
| PUT | `/api/clusters/{name}/config` | Update cluster config |

## Configuration

### Backend Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `REGISTRY_URL` | `http://localhost:8080` | Registry service URL |
| `ETCD_HOST` | `localhost` | ETCD host address |
| `ETCD_PORT` | `2379` | ETCD port |
| `ETCD_TIMEOUT` | `10` | ETCD connection timeout (seconds) |
| `ETCD_CONFIG_PREFIX` | `/joblens/config/` | Mode/role/rule storage prefix |
| `ETCD_REGISTRY_PREFIX` | `/joblens_registry/services/` | Service attribute storage prefix |
| `ETCD_CLUSTERS_INSTANCE_PREFIX` | `/joblens_registry/clusters/instance/` | Cluster instance storage prefix |
| `COLLECTOR_TIMEOUT` | `5.0` | Collector request timeout (seconds) |
| `CACHE_TTL` | `30` | Cache TTL (seconds) |
| `DEBUG` | `false` | Debug mode |
| `LOG_LEVEL` | `INFO` | Log level |

### Frontend Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Backend API base URL |
| `VITE_REFRESH_INTERVAL` | `30000` | Auto-refresh interval (ms) |
| `VITE_DEFAULT_LANG` | `zh-CN` | Default language |

## Development Guide

### Backend

- All requests are proxied through FastAPI; backend services are never directly exposed
- ETCD is used as the sole data store, with no traditional relational database
- On startup, default mode and default role are automatically initialized
- Service attributes (mode/role) are read from ETCD, service status is fetched from the registry, and both are merged in responses
- Lua rules are validated for syntax and structure on the Python side via the `lupa` library
- Configuration changes are automatically saved as version history and support rollback

### Frontend

- API calls are centralized in `src/api/`, all HTTP requests go through a unified Axios instance
- Language packs are in `src/locales/{zh-CN,en}.ts`; new text must be added to both files
- Page views follow Element Plus component conventions

### Testing

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm run test:unit    # Vitest unit tests
npm run test:e2e     # Playwright E2E tests
npm run type-check   # TypeScript type checking
npm run lint         # ESLint code linting
```

## Troubleshooting

### Backend fails to start
- Verify Python 3.10+ is installed
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if ETCD is reachable and port 2379 is open

### Frontend cannot connect to backend
- Verify the `VITE_API_BASE_URL` configuration
- Ensure the backend service is running
- Check the browser console for CORS errors

### Service list is empty
- Verify the `REGISTRY_URL` configuration
- Ensure the registry service is running with registered service nodes
- Check backend logs for detailed error information

## License

[Apache License 2.0](LICENSE)
