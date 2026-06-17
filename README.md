# JobLens Web Manager

A web management platform for the JobLens distributed job scheduling system, built with a decoupled frontend-backend architecture.

[中文](README_CN.md)

## Architecture

```
Browser → Vue 3 Frontend → FastAPI Backend Proxy → Registry / JobLens Agent (Collector)
                                                      │
                                                  ETCD (Config Storage)
```

The backend communicates with the external registry service via HTTP to retrieve service listings, uses ETCD for all configuration data (modes, roles, rules, cluster configs, service attributes), and interacts with JobLens agents on each node for job management and performance collection.

## Features

- **Dashboard** — Service health overview, cluster tag distribution, status charts
- **Service Management** — View, filter, edit, and deregister service nodes; health checks via registry + collector
- **Job Management** — Create, view, and delete jobs (standard and Condor)
- **Configuration Management** — Dynamic mode management with YAML editing and version history
- **Role & Rule Management** — Hierarchical role tree with Lua rule editor and inheritance
- **Cluster Management** — Configure cluster properties, aliases, and extended fields
- **Internationalization** — Auto-detects browser language; supports Chinese and English
- **Authentication** — JWT-based login with IP whitelist bypass

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 20+ (see `engines` in `frontend/package.json`)
- ETCD 3.x
- JobLens Registry (optional, some features depend on it)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Configure: edit backend/.env
uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install

# Configure: edit frontend/.env
npm run dev
```

Access: http://localhost:5173

### Docker

```bash
cd backend && docker build -t joblens-webmanager-backend .
cd frontend && docker build -t joblens-webmanager-frontend .
```

## Project Structure

```
joblens_web_manager/
├── backend/           # Python + FastAPI + ETCD
│   ├── backend/       # Application code
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # Vue 3 + TypeScript + Vite
│   ├── src/           # Application code
│   ├── package.json
│   └── Dockerfile
├── doc/               # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── CONFIGURATION.md
│   └── DEVELOPMENT.md
├── README.md
├── README_CN.md
└── LICENSE
```

## Documentation

| Document | Description |
|----------|-------------|
| [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) | Full architecture overview, data models, and component details |
| [doc/API.md](doc/API.md) | Complete API endpoint reference |
| [doc/CONFIGURATION.md](doc/CONFIGURATION.md) | Backend and frontend configuration options |
| [doc/DEVELOPMENT.md](doc/DEVELOPMENT.md) | Development guide, testing, and troubleshooting |

## License

[Apache License 2.0](LICENSE)
