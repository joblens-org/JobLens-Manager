# JobLens Web Manager — API Reference

All business API endpoints require JWT authentication (except `/api/auth/login` and `/health`).

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login with password, returns JWT token |

### Request
```json
{
  "password": "admin"
}
```

### Response
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> **IP Whitelist**: If `AUTH_WHITELIST_IPS` is configured, requests from whitelisted IPs bypass authentication entirely.

---

## Service Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/services` | Service list (paginated, filtered, sorted, searched) |
| GET | `/api/services/count` | Total service count |
| GET | `/api/services/registry/health` | Registry health status |
| GET | `/api/services/registry/stats` | Registry statistics |
| GET | `/api/services/cluster/tags` | Cluster tag list |
| GET | `/api/services/{id}` | Service details |
| GET | `/api/services/{id}/health` | Service health status (registry + collector) |
| PUT | `/api/services/{id}/attributes` | Update service attributes (mode/role) |
| DELETE | `/api/services/{id}` | Deregister service |

### Query Parameters for `GET /api/services`
- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20)
- `sort_by` — Sort field
- `sort_order` — `asc` or `desc`
- `search` — Keyword search
- `status` — Filter by status (`healthy`/`unhealthy`)
- `mode` — Filter by mode name
- `role_id` — Filter by role ID

---

## Job Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/jobs` | Job list |
| GET | `/api/jobs/{job_id}` | Job details |
| POST | `/api/jobs` | Create job (condor/common) |
| DELETE | `/api/jobs/{job_id}` | Delete job |
| GET | `/api/jobs/{service_id}/count` | Job count for a service |

---

## Metrics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/metrics/services/{id}/collectors` | Collector performance metrics |
| GET | `/api/metrics/services/{id}/writers` | Writer performance metrics |
| GET | `/api/metrics/services/{id}/writers/{name}` | Writer details |
| GET | `/api/metrics/services/{id}/all` | All metrics combined |
| GET | `/api/metrics/services/{id}/prometheus` | Prometheus-compatible metrics |
| GET | `/api/metrics/registry` | Registry metrics |

---

## Config Management (Legacy)

> **Note**: Use `/api/modes` endpoints for new implementations. These legacy endpoints are kept for backward compatibility.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/configs/{mode}` | Get config for a mode |
| PUT | `/api/configs/{mode}` | Update config for a mode |
| GET | `/api/configs/{mode}/versions` | Config version history |
| GET | `/api/configs/{mode}/version/{version}` | Specific version config |
| POST | `/api/configs/{mode}/rollback/{version}` | Rollback to a specific version |
| GET | `/api/configs/health` | Config health check |
| GET | `/api/configs/modes` | Available config modes |

---

## Mode Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/modes` | Mode list |
| POST | `/api/modes` | Create a new mode |
| GET | `/api/modes/{name}` | Mode details |
| PUT | `/api/modes/{name}` | Update mode metadata |
| DELETE | `/api/modes/{name}` | Delete a mode |
| GET | `/api/modes/{name}/config` | Get mode YAML config |
| PUT | `/api/modes/{name}/config` | Update mode YAML config |
| GET | `/api/modes/{name}/versions` | Config version history |
| GET | `/api/modes/{name}/version/{v}` | Specific version config |
| POST | `/api/modes/{name}/rollback/{v}` | Rollback to a version |
| GET | `/api/modes/default` | Get the default mode |

---

## Role Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/roles` | Role list |
| POST | `/api/roles` | Create a new role |
| GET | `/api/roles/{id}` | Role details (with rule info) |
| PUT | `/api/roles/{id}` | Update role |
| DELETE | `/api/roles/{id}` | Delete role |
| GET | `/api/roles/{id}/rules` | Role rules (with inherited rules) |
| GET | `/api/roles/{id}/rules/effective` | Effective rules (deduplicated) |
| GET | `/api/roles/default` | Get the default role |

---

## Rule Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/rules` | Rule list (paginated) |
| POST | `/api/rules` | Create a new rule |
| GET | `/api/rules/{id}` | Rule details |
| PUT | `/api/rules/{id}` | Update rule |
| DELETE | `/api/rules/{id}` | Delete rule |

### Request Body for `POST /api/rules`
```json
{
  "role_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "validation-rule",
  "lua_content": "function validate(data) return true end",
  "metadata": {"category": "validation"}
}
```

---

## Cluster Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/clusters` | Cluster list (auto-discovered + configured) |
| GET | `/api/clusters/scheme` | Cluster condensed view |
| GET | `/api/clusters/{name}` | Cluster details |
| PUT | `/api/clusters/{name}/config` | Update cluster config |

### Request Body for `PUT /api/clusters/{name}/config`
```json
{
  "alias": "Production Condor",
  "description": "Beijing datacenter cluster",
  "enabled": true,
  "extra": {
    "es_url": "http://localhost:9200",
    "es_username": "elastic",
    "es_password": "changeme",
    "default_node_port": 7592,
    "script_path": "/opt/joblens/scripts"
  }
}
```

### Required Extra Fields
The `extra` object should include these 5 fields for full functionality:
- `es_url` — ElasticSearch URL
- `es_username` — ES username
- `es_password` — ES password
- `default_node_port` — Default node port
- `script_path` — Script path

---

## Health Check (Public)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check endpoint (no auth required) |

---

## Common Response Format

### Success
```json
{
  "data": { ... },
  "total": 42
}
```

### Error
```json
{
  "detail": "Error description"
}
```
