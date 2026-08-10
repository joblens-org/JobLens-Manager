# JobLens Web Manager — Configuration Reference

## Backend Configuration (`backend/.env`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `REGISTRY_URL` | `http://localhost:8080` | Registry service URL |
| `COLLECTOR_TIMEOUT` | `5.0` | Collector request timeout (seconds) |
| `CACHE_TTL` | `30` | In-memory cache TTL (seconds) |
| `ETCD_HOST` | `localhost` | ETCD host address |
| `ETCD_PORT` | `2379` | ETCD port |
| `ETCD_TIMEOUT` | `10` | ETCD connection timeout (seconds) |
| `ETCD_CONFIG_PREFIX` | `/joblens/config/` | Prefix for mode/role/rule storage |
| `ETCD_REGISTRY_PREFIX` | `/joblens_registry/services/` | Prefix for service attributes |
| `ETCD_CLUSTERS_INSTANCE_PREFIX` | `/joblens_registry/clusters/instance/` | Prefix for cluster instances |
| `DEBUG` | `false` | Debug mode (enables detailed logging) |
| `LOG_LEVEL` | `INFO` | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`) |
| `LOG_PATH` | `./joblens_web_manager.log` | Log file path |
| `ADMIN_PASSWORD` | `admin` | Admin login password |
| `AUTH_WHITELIST_IPS` | *(empty)* | Whitelisted IPs, comma-separated, supports CIDR (e.g. `127.0.0.1,10.0.0.0/8`). Requests from these IPs bypass authentication |
| `TRUST_PROXY_HEADERS` | `false` | Trust proxy headers (`X-Forwarded-For`, `X-Real-IP`) for client IP resolution. **Only enable when behind a trusted proxy that sets these headers correctly, otherwise clients can spoof their IP** |
| `DEFAULT_MODE_NAME` | `default` | Default mode created on first startup |
| `DEFAULT_ROLE_NAME` | `default` | Default role created on first startup |

### Example `backend/.env`
```env
REGISTRY_URL=http://localhost:8080
COLLECTOR_TIMEOUT=5.0
CACHE_TTL=30
ETCD_HOST=localhost
ETCD_PORT=2379
DEBUG=false
LOG_LEVEL=INFO
LOG_PATH=./joblens_web_manager.log
ADMIN_PASSWORD=admin
AUTH_WHITELIST_IPS=127.0.0.1,10.0.0.0/8
DEFAULT_MODE_NAME=default
DEFAULT_ROLE_NAME=default
```

> All parameters are defined in [backend/backend/config.py](backend/backend/config.py). The `Settings` class uses `pydantic-settings` with priority: **environment variables > `.env` file > defaults**.

### URL Validation
The `REGISTRY_URL` is automatically validated: if no protocol is specified, `http://` is prepended. Whitespace is trimmed.

---

## Frontend Configuration (`frontend/.env`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Backend API base URL |
| `VITE_REFRESH_INTERVAL` | `30000` | Dashboard auto-refresh interval (ms) |
| `VITE_DEFAULT_LANG` | `zh-CN` | Default language (`zh-CN` or `en`) |

### Example `frontend/.env`
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_REFRESH_INTERVAL=30000
VITE_DEFAULT_LANG=zh-CN
```

---

## ETCD Storage Structure

```
/joblens/config/
├── /modes/                 # Mode definitions
│   └── {mode_name}/
│       ├── info            # Mode metadata
│       ├── config          # Current YAML config
│       └── versions/{ts}/  # Historical versions
├── /roles/                 # Role definitions
│   └── {role_id}/
│       ├── info            # Role metadata
│       └── rules           # Associated rule IDs
└── /rules/                 # Rule definitions
    └── {rule_id}/
        ├── info            # Rule metadata
        └── content         # Lua content

/joblens_registry/
├── /services/              # Service attributes (mode, role_id)
└── /clusters/instance/     # Auto-discovered cluster instances
```

---

## Docker Configuration

Both backend and frontend provide `Dockerfile` for independent image builds.

### Backend Dockerfile
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 80
CMD ["npx", "serve", "dist", "-l", "80"]
```
