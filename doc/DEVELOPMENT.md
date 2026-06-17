# JobLens Web Manager — Development Guide

## Development Guide

### Backend

- All requests are proxied through FastAPI; backend services are never directly exposed
- ETCD is used as the sole data store, with no traditional relational database
- On startup, default mode and default role are automatically initialized via `db_init.py`
- Service attributes (mode/role) are read from ETCD, service status is fetched from the registry, and both are merged in responses
- Lua rules are validated for syntax and structure on the Python side via the `lupa` library
- Configuration changes are automatically saved as version history and support rollback
- JWT authentication is required for all business API endpoints; only `/api/auth/login` and `/health` are public
- IP whitelist allows bypassing authentication for trusted IP addresses

### Frontend

- API calls are centralized in `src/api/`, all HTTP requests go through a unified Axios instance
- Language packs are in `src/locales/{zh-CN,en}.ts`; new text must be added to both files
- Page views follow Element Plus component conventions
- Authentication state is managed via Pinia store in `src/stores/auth.ts`
- Route guards enforce login requirement; unauthenticated users are redirected to `/login`

## Testing

### Backend Tests
```bash
cd backend
pytest
```

Test dependencies are in `requirements-test.txt`. The `pytest.ini` file configures test discovery and coverage.

### Frontend Tests
```bash
cd frontend
npm run test        # Vitest unit tests (run once)
npm run test:watch  # Vitest watch mode
npm run type-check  # TypeScript type checking via vue-tsc
npm run lint        # ESLint code linting with auto-fix
npm run format      # Prettier formatting
```

### Available Scripts (from `frontend/package.json`)
| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `vite` | Development server with HMR |
| `build` | `run-p type-check "build-only {@}" --` | Production build with type checking |
| `build-only` | `vite build` | Build without type checking |
| `preview` | `vite preview` | Preview production build locally |
| `type-check` | `vue-tsc --build` | TypeScript type checking |
| `lint` | `eslint . --fix --cache` | ESLint with auto-fix |
| `format` | `prettier --write --experimental-cli src/` | Prettier formatting |
| `test` | `vitest run` | Run unit tests once |
| `test:watch` | `vitest` | Run unit tests in watch mode |

## Code Standards

- **Python**: Use Black formatter, follow PEP 8
- **TypeScript**: Use ESLint and Prettier
- **Vue**: Use Vue 3 Composition API with `<script setup lang="ts">`
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

## Troubleshooting

### Backend fails to start
- Verify Python 3.10+ is installed
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if ETCD is reachable and port 2379 is open
- Check `backend/.env` configuration is valid

### Frontend cannot connect to backend
- Verify the `VITE_API_BASE_URL` configuration in `frontend/.env`
- Ensure the backend service is running on the expected port
- Check the browser console for CORS errors
- Verify network connectivity between frontend and backend

### Service list is empty
- Verify the `REGISTRY_URL` configuration in `backend/.env`
- Ensure the registry service is running with registered service nodes
- Check backend logs for detailed error information
- Verify ETCD is accessible and contains service data

### Login fails
- Verify `ADMIN_PASSWORD` configuration in `backend/.env`
- Check if your IP is in `AUTH_WHITELIST_IPS` (if set, whitelisted IPs bypass password login)
- Ensure the backend is running and the `/api/auth/login` endpoint is accessible
- Check browser DevTools Network tab for the exact error response

### Mode/Role APIs return 404
- Check backend routes are correctly registered in `main.py`
- Verify API path prefixes (`/api/modes/`, `/api/roles/`)
- Check backend logs for import errors or startup exceptions

### Filter functionality not working
- Check service data contains `mode` and `role_id` fields
- Verify filter parameters are correctly passed to the API
- Check mode and role list API responses are valid
- Verify ETCD contains the expected mode/role data

## Debugging Tips

### Backend Debugging
```bash
# Run with auto-reload and detailed logging
uvicorn backend.main:app --reload --port 8000

# Visit Swagger UI to test APIs interactively
open http://localhost:8000/docs
```

### Frontend Debugging
- Use Vue DevTools browser extension to inspect component state and Pinia stores
- Browser Developer Tools → Network tab to inspect API requests and responses
- Console tab for errors, warnings, and `console.log` output

## Adding New Features

### Backend Development Flow
1. Add/update data model in `backend/models/`
2. Add/update API route in `backend/routers/`
3. Register route in `backend/main.py` (if new router)
4. Update `backend/requirements.txt` if new dependencies are needed
5. Add tests in `backend/tests/`

### Frontend Development Flow
1. Add/update API client in `frontend/src/api/`
2. Add/update page component in `frontend/src/views/`
3. Add/update route in `frontend/src/router/index.ts` (if new page)
4. Add/update navigation menu in `frontend/src/App.vue` (if new page)
5. Update both language files in `frontend/src/locales/` (if new text)
6. Add tests in `frontend/src/**/*.test.ts` or `frontend/tests/`
