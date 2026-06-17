# JobLens Web Manager - Architecture and Features

## Project Overview

**JobLens Web Manager** is a decoupled web monitoring and management system for managing and monitoring JobLens service clusters. The system communicates with a registry center (port 8080) and collectors (port 7592) through a Python backend proxy, providing a unified management interface.

### Main Use Cases
- Service node registration and health monitoring
- Job management and scheduling
- Configuration management and version control
- Role and rule management (with inheritance)
- Mode and filter management
- Cluster management
- Authentication and authorization

### Tech Stack
- **Backend**: FastAPI + Python + ETCD storage
- **Frontend**: Vue 3 + TypeScript + Element Plus UI
- **Storage**: ETCD (config, modes, roles, rules, cluster configs, service attributes)
- **Communication**: HTTP RESTful API
- **Authentication**: JWT + IP Whitelist

### Project Structure
```
joblens_web_manager/
├── README.md                 # Project documentation (English)
├── README_CN.md              # Project documentation (Chinese)
├── doc/                      # Documentation
│   ├── ARCHITECTURE.md       # Architecture description (this document)
│   ├── API.md                # API reference
│   ├── CONFIGURATION.md      # Configuration reference
│   └── DEVELOPMENT.md        # Development guide
├── backend/                  # Python backend
│   ├── backend/
│   │   ├── main.py          # FastAPI main application (route registration)
│   │   ├── config.py        # Configuration (ETCD connection, registry URL, etc.)
│   │   ├── models/          # Pydantic data models
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Auth models (LoginRequest, LoginResponse)
│   │   │   ├── cluster.py      # Cluster models (ClusterInfo, ClusterConfig, ClusterDetail)
│   │   │   ├── etcd_config.py  # ETCD config models
│   │   │   ├── job.py          # Job models
│   │   │   ├── metrics.py      # Metrics models
│   │   │   ├── mode.py         # Mode models (ModeInfo, etc.)
│   │   │   ├── role.py         # Role and rule models (RoleInfo, RuleInfo, etc.)
│   │   │   └── service.py      # Service models (ServiceInfo, ServiceHealth, etc.)
│   │   ├── routers/         # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication (login)
│   │   │   ├── clusters.py     # Cluster management
│   │   │   ├── configs.py      # Config management (legacy, mode-based)
│   │   │   ├── jobs.py         # Job management
│   │   │   ├── metrics.py      # Metrics monitoring
│   │   │   ├── modes.py        # Mode management
│   │   │   ├── roles.py        # Role management
│   │   │   ├── rules.py        # Rule management
│   │   │   └── services.py     # Service management (enhanced filtering)
│   │   └── services/        # Business logic services
│   │       ├── __init__.py
│   │       ├── collector_service.py  # Collector service
│   │       ├── lua_validator.py      # Lua rule validator
│   │       └── registry_service.py   # Registry service
│   ├── requirements.txt     # Python dependencies
│   ├── .env                # Environment variables
│   └── venv/               # Python virtual environment
├── frontend/               # Vue frontend
│   ├── src/
│   │   ├── api/           # API clients
│   │   │   ├── auth.ts       # Auth API (login)
│   │   │   ├── cluster.ts    # Cluster API
│   │   │   ├── config.ts    # Axios instance & Config API
│   │   │   ├── index.ts     # API exports
│   │   │   ├── job.ts       # Job API
│   │   │   ├── metrics.ts   # Metrics API
│   │   │   ├── modes.ts     # Mode API
│   │   │   ├── roles.ts     # Role API
│   │   │   ├── rules.ts     # Rule API
│   │   │   └── service.ts   # Service API (enhanced filtering)
│   │   ├── assets/        # Static assets
│   │   ├── components/    # Shared components
│   │   │   └── TimezoneSelect.vue   # Timezone picker
│   │   ├── router/        # Route configuration
│   │   │   └── index.ts   # Vue router (includes login, clusters, roles routes)
│   │   ├── stores/        # Pinia state management
│   │   │   └── auth.ts     # Auth store (login/logout/token)
│   │   ├── views/         # Page views
│   │   │   ├── ClusterManager.vue    # Cluster management
│   │   │   ├── ConfigManager.vue     # Config management (multi-mode support)
│   │   │   ├── Dashboard.vue         # Dashboard
│   │   │   ├── JobManager.vue        # Job management
│   │   │   ├── LoginView.vue         # Login page
│   │   │   ├── RoleManager.vue       # Role management
│   │   │   ├── ServiceDetail.vue     # Service detail (mode/role display)
│   │   │   └── ServiceList.vue       # Service list (enhanced filtering)
│   │   ├── App.vue        # Main application (layout, navigation, install dialog)
│   │   └── main.ts        # Application entry
│   ├── package.json       # Frontend dependencies
│   ├── .env              # Frontend environment variables
│   └── public/           # Public files
├── app.py                # JobLens collector (external service)
└── LICENSE               # Apache 2.0
```

## Feature Modules

### 1. Dashboard
- Service status statistics (total, healthy, unhealthy, active)
- Service status distribution charts (using ECharts)
- Recent service list
- Registry health monitoring

### 2. Service Management
#### Service List (ServiceList.vue)
- View all registered service nodes
- Filter services by mode
- Filter services by role
- Filter for healthy services only
- Service detail view and deregistration
- Display service mode and role information

#### Service Detail (ServiceDetail.vue)
- Service basic information display
- Service health check (registry + collector)
- Mode and role information display
- Associated job list
- Performance metrics view

### 3. Job Management (JobManager.vue)
- View job list across all services
- Add new jobs (standard and Condor jobs)
- Delete jobs
- View job details
- Job count statistics

### 4. Configuration Management (ConfigManager.vue)
**Original functionality:**
- Develop/Test environment config management
- YAML config editing
- Config version history

**Current functionality:**
- Dynamic mode management system (replaces static environment concept)
- Multi-mode config editing (create, edit, delete modes)
- Mode config version management
- YAML editor (Monaco Editor with syntax highlighting and validation)

> Note: Both `/api/configs` (legacy) and `/api/modes` (current) routes exist for backward compatibility.

### 5. Role and Rule Management (RoleManager.vue)
**Role Management:**
- Role tree structure display (supports inheritance)
- Role create, edit, delete
- Role inheritance mechanism (parent-child relationship)
- Role-associated service count statistics

**Rule Management:**
- Lua rule editor (code highlighting, syntax checking via `lupa`)
- Rule create, edit, delete
- Rules are associated with roles via `role_id`
- Rule merging: child role rules with same ID override parent role rules
- Effective rules preview (deduplicated)

### 6. Cluster Management (ClusterManager.vue)
- Left-side cluster tree (searchable by name)
- Basic configuration: alias, description, enabled status
- Extended required configuration: ES address/username/password, node port, script path, timezone, index pattern
- Free-form extension fields (JSON format)
- Cluster condensed view (Scheme)
- Missing required fields detection and display

### 7. Internationalization
- Chinese (zh-CN) and English (en)
- Auto-detects browser language, supports manual switching with persistence

### 8. Authentication
- JWT-based login with password authentication
- IP whitelist bypass for trusted IPs (supports CIDR notation like `10.0.0.0/8`)
- Frontend route guards with automatic redirect to login page
- Logout functionality
- All business API endpoints require JWT token; only `/api/auth/login` and `/health` are public

## Technical Architecture

### Backend Architecture (FastAPI)
```
FastAPI Application (backend/main.py)
├── CORS middleware configuration
├── Request logging middleware
├── Route Registration
│   ├── /api/auth/*        (auth.router)      - Public
│   ├── /api/services/*    (services.router) - JWT protected
│   ├── /api/jobs/*        (jobs.router)     - JWT protected
│   ├── /api/metrics/*     (metrics.router)  - JWT protected
│   ├── /api/configs/*     (configs.router)  - JWT protected
│   ├── /api/modes/*       (modes.router)    - JWT protected
│   ├── /api/roles/*       (roles.router)    - JWT protected
│   ├── /api/rules/*       (rules.router)    - JWT protected
│   └── /api/clusters/*    (clusters.router) - JWT protected
├── ETCD client connection pool
└── Business Service Layer
    ├── RegistryService (registry communication)
    ├── CollectorService (collector communication)
    └── LuaValidator (Lua rule validation)
```

### Frontend Architecture (Vue 3)
```
Vue Application (frontend/src/main.ts)
├── Router system (router/index.ts) - 8 routes including login
├── Global state management (stores/auth.ts)
├── API client layer (api/)
├── Page components (views/)
├── Shared components (components/)
└── Element Plus UI component library
```

### Data Storage Architecture
```
ETCD Key-Value Storage
├── /services/                    # Service registration info (from registry)
├── /jobs/                       # Job information
├── /configs/{mode}/             # Mode config (legacy path)
│   ├── /config.yaml            # Current config
│   └── /versions/{timestamp}/  # Version history
├── /modes/                      # Mode definitions
├── /roles/                      # Role definitions
├── /rules/                      # Rule definitions
├── /clusters/                   # Cluster configurations
└── /auth/                       # Authentication data (if any)
```

### Frontend-Backend Communication
- **Protocol**: HTTP RESTful API
- **Authentication**: JWT token in `Authorization` header; IP whitelist bypass
- **Data Format**: JSON
- **Error Handling**: Standardized error response format
- **CORS**: Configured to allow all origins (development environment)

## Data Models

### Service Model (ServiceInfo)
```python
class ServiceInfo(BaseModel):
    service_id: str          # Service ID
    host: str               # Host address
    port: int               # Port
    name: str               # Service name
    version: str            # Version
    base_url: str           # Base URL
    status: str             # Status (healthy/unhealthy)
    registered_at: datetime # Registration time
    last_heartbeat: Optional[datetime]  # Last heartbeat
    mode: Optional[str]     # Associated mode name
    role_id: Optional[str]  # Associated role ID
    metadata: Optional[dict]  # Metadata
    
    @computed_field
    @property
    def healthy(self) -> bool:
        return self.status == "healthy"
```

### Mode Model (ModeInfo)
```python
class ModeInfo(BaseModel):
    name: str               # Mode name (unique identifier)
    description: Optional[str]  # Mode description
    created_at: datetime    # Creation time
    updated_at: datetime    # Update time
    default: bool           # Whether this is the default mode
    config_count: int       # Number of associated configs
```

### Role Model (RoleInfo)
```python
class RoleInfo(BaseModel):
    role_id: str            # Role ID (UUID)
    name: str               # Role name (unique)
    description: Optional[str]  # Role description
    parent_role_id: Optional[str]  # Parent role ID (inheritance)
    rule_ids: List[str]     # Associated rule ID list
    created_at: datetime    # Creation time
    updated_at: datetime    # Update time
    service_count: int      # Number of services using this role
    default: bool           # Whether this is the default role
    metadata: Optional[Dict[str, Any]]  # Role metadata
```

### Rule Model (RuleInfo)
```python
class RuleInfo(BaseModel):
    rule_id: str            # Rule ID (UUID)
    role_id: str            # Associated role ID (UUID)
    name: str               # Rule name
    lua_content: str        # Lua rule content
    created_at: datetime    # Creation time
    updated_at: datetime    # Update time
    version: int            # Version number
    metadata: Optional[Dict[str, Any]]  # Rule metadata
```

### Cluster Model (ClusterDetail)
```python
class ClusterDetail(BaseModel):
    cluster_name: str       # Cluster name
    cluster_type: str       # Cluster type (e.g., condor/slurm)
    tags: list[str]         # Cluster tags
    alias: str              # Alias
    description: str        # Description
    enabled: bool           # Whether enabled
    extra: dict             # Extended config fields (JSON)
    missing_fields: list[str]  # List of unconfigured required fields
    updated_at: Optional[datetime]  # Last update time
```

## API Endpoints

### Authentication (/api/auth)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| POST | `/login` | Login | Password authentication, returns JWT token |

### Service Management (/api/services)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/services` | Get service list | Supports pagination, filtering, sorting, searching |
| GET | `/services/count` | Service count | |
| GET | `/services/registry/health` | Registry health | |
| GET | `/services/registry/stats` | Registry statistics | |
| GET | `/services/cluster/tags` | Cluster tags | |
| GET | `/services/{id}` | Service details | |
| GET | `/services/{id}/health` | Service health | |
| PUT | `/services/{id}/attributes` | Update attributes | Update mode and role |
| DELETE | `/services/{id}` | Deregister service | |

### Job Management (/api/jobs)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/jobs` | Job list | |
| GET | `/jobs/{job_id}` | Job details | |
| POST | `/jobs` | Create job | Supports condor/common |
| DELETE | `/jobs/{job_id}` | Delete job | |
| GET | `/jobs/{service_id}/count` | Job count | |

### Metrics (/api/metrics)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/services/{id}/collectors` | Collector performance | |
| GET | `/services/{id}/writers` | Writer performance | |
| GET | `/services/{id}/writers/{name}` | Writer details | |
| GET | `/services/{id}/all` | All metrics | |
| GET | `/services/{id}/prometheus` | Prometheus metrics | |
| GET | `/registry` | Registry metrics | |

### Config Management (/api/configs) - Legacy
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/{mode}` | Get config | |
| PUT | `/{mode}` | Update config | |
| GET | `/{mode}/versions` | Version history | |
| GET | `/{mode}/version/{v}` | Specific version | |
| POST | `/{mode}/rollback/{v}` | Rollback | |
| GET | `/health` | Health check | |
| GET | `/modes` | Config modes | |

### Mode Management (/api/modes)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/modes` | Mode list | |
| POST | `/modes` | Create mode | |
| GET | `/modes/{name}` | Mode details | |
| PUT | `/modes/{name}` | Update mode | |
| DELETE | `/modes/{name}` | Delete mode | |
| GET | `/modes/{name}/config` | Get mode config | |
| PUT | `/modes/{name}/config` | Update mode config | |
| GET | `/modes/{name}/versions` | Version history | |
| GET | `/modes/{name}/version/{v}` | Specific version | |
| POST | `/modes/{name}/rollback/{v}` | Rollback | |
| GET | `/modes/default` | Get default mode | |

### Role Management (/api/roles)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/roles` | Role list | |
| POST | `/roles` | Create role | |
| GET | `/roles/{id}` | Role details | Includes rule info |
| PUT | `/roles/{id}` | Update role | |
| DELETE | `/roles/{id}` | Delete role | |
| GET | `/roles/{id}/rules` | Role rules | With inheritance |
| GET | `/roles/{id}/rules/effective` | Effective rules | Deduplicated |
| GET | `/roles/default` | Get default role | |

### Rule Management (/api/rules)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/rules` | Rule list | Paginated |
| POST | `/rules` | Create rule | |
| GET | `/rules/{id}` | Rule details | |
| PUT | `/rules/{id}` | Update rule | |
| DELETE | `/rules/{id}` | Delete rule | |

### Cluster Management (/api/clusters)
| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/clusters` | Cluster list | |
| GET | `/clusters/scheme` | Cluster condensed view | |
| GET | `/clusters/{name}` | Cluster details | |
| PUT | `/clusters/{name}/config` | Update cluster config | |

## Frontend Component Structure

### Route Configuration (router/index.ts)
```typescript
const routes = [
  { path: '/login', name: 'login', component: LoginView },
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/services', name: 'services', component: ServiceList },
  { path: '/services/:id', name: 'service-detail', component: ServiceDetail, props: true },
  { path: '/jobs', name: 'jobs', component: JobManager },
  { path: '/configs', name: 'configs', component: ConfigManager },
  { path: '/roles', name: 'roles', component: RoleManager },
  { path: '/clusters', name: 'clusters', component: ClusterManager },
]
```

### Navigation Menu (App.vue)
```javascript
const menuItems = [
  { path: '/', icon: 'Monitor', label: i18n('nav.dashboard') },
  { path: '/services', icon: 'Service', label: i18n('nav.services') },
  { path: '/jobs', icon: 'Document', label: i18n('nav.jobs') },
  { path: '/configs', icon: 'Setting', label: i18n('nav.configs') },
  { path: '/roles', icon: 'User', label: i18n('nav.roles') },
  { path: '/clusters', icon: 'Monitor', label: i18n('nav.clusters') },
]
```

### Key Component Features

#### LoginView.vue
- Username/password login form
- JWT token storage in localStorage
- Redirect to original page after login
- Auto-redirect to dashboard if already logged in

#### RoleManager.vue
- Role tree component: displays role inheritance hierarchy
- Rule editor: integrated CodeMirror Lua code editor
- Inheritance management: handles parent-child role relationships
- Rule management: create, edit, delete rules associated with roles

#### ConfigManager.vue (Refactored)
- Mode selector: dynamically loads mode list, supports mode creation
- Multi-tab: each mode has independent tab, supports parallel editing
- Config version: each mode's config version history independently managed
- YAML editor (Monaco Editor)

#### ServiceList.vue (Enhanced)
- Filter controls: mode and role dropdown filters
- Dynamic options: filter options loaded from API
- Table columns: mode and role display columns

#### ClusterManager.vue
- Left-side cluster tree with search
- Config form with required fields validation
- Extra fields JSON editor
- Missing required fields highlighting

## Deployment and Running

### Backend Deployment
1. **Environment Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables** (backend/.env):
   ```env
   REGISTRY_URL=http://localhost:8080
   COLLECTOR_TIMEOUT=5.0
   CACHE_TTL=30
   ETCD_HOST=localhost
   ETCD_PORT=2379
   ADMIN_PASSWORD=admin
   AUTH_WHITELIST_IPS=127.0.0.1,10.0.0.0/8
   ```

3. **Run Service**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

4. **API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Frontend Deployment
1. **Environment Setup**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment Variables** (frontend/.env):
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api
   VITE_REFRESH_INTERVAL=30000
   VITE_DEFAULT_LANG=zh-CN
   ```

3. **Development Mode**:
   ```bash
   npm run dev
   ```

4. **Production Build**:
   ```bash
   npm run build
   ```

### Testing

**Backend Testing**:
```bash
cd backend
pytest
```

**Frontend Testing**:
```bash
cd frontend
npm run test        # Vitest unit tests
npm run test:watch  # Vitest watch mode
npm run type-check  # TypeScript type checking
npm run lint        # ESLint code linting
npm run format      # Prettier formatting
```

## Code Standards
- **Python**: Use Black formatter, follow PEP 8
- **TypeScript**: Use ESLint and Prettier
- **Vue**: Use Vue 3 Composition API
- **Commits**: Follow Conventional Commits

## Troubleshooting

### Common Issues
1. **Backend cannot connect to ETCD**:
   - Check ETCD service status
   - Verify `ETCD_HOST` and `ETCD_PORT` configuration
   - Check network connection and firewall

2. **Frontend cannot connect to backend**:
   - Check `VITE_API_BASE_URL` configuration
   - Verify backend service is running
   - Check browser console for CORS errors

3. **Mode/Role APIs return 404**:
   - Check backend routes are correctly registered
   - Verify API path prefixes (`/api/modes/`, `/api/roles/`)
   - Check backend logs for import errors

4. **Login fails**:
   - Verify `ADMIN_PASSWORD` is set correctly in `backend/.env`
   - Check if your IP is in `AUTH_WHITELIST_IPS` (whitelisted IPs bypass password login)
   - Ensure backend is running and accessible

5. **Filter functionality not working**:
   - Check service data contains mode and role_id fields
   - Verify filter parameters are correctly passed to API
   - Check mode and role list API responses

### Debugging Tips
1. **Backend Debugging**:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   - Visit `http://localhost:8000/docs` to test APIs
   - Check console log output

2. **Frontend Debugging**:
   - Use Vue DevTools to inspect component state
   - Browser developer tools to view network requests
   - Console for errors and warnings

## Extension Plans

### Short-term Improvements
1. **Data migration scripts**: Automate migration from existing environments to modes
2. **Role-based UI permissions**: UI access control based on roles
3. **Rule syntax validation**: Lua syntax checking and validation
4. **Batch operations**: Batch mode and role assignment for services

### Long-term Planning
1. **Audit logging**: Record all config and rule changes
2. **Notification system**: Config change and service status alerts
3. **Multi-tenant support**: Multi-team/project isolation
4. **API key management**: Secure API access control

---

**Document Version**: 1.1
**Last Updated**: 2026-06-17
**Maintainer**: JobLens Development Team
