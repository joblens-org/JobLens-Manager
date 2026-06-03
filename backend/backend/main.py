from fastapi import FastAPI, Request, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routers import services, jobs, metrics, configs, modes, roles, rules, clusters, auth
from contextlib import asynccontextmanager
from backend.common.logger import logger
from backend.common import initialize_etcd
from backend.common.auth import verify_token
from backend.config import settings
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_etcd()
    yield

app = FastAPI(title="JobLens Web Manager API", version="1.0.0", debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求中间件日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求开始
    logger.info(f"请求开始: {request.method} {request.url.path}")
    logger.debug(f"请求头: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # 记录请求完成
        logger.info(
            f"请求完成: {request.method} {request.url.path} "
            f"状态码: {response.status_code} 耗时: {process_time:.2f}ms"
        )
        
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"请求异常: {request.method} {request.url.path} "
            f"错误: {str(e)} 耗时: {process_time:.2f}ms"
        )
        raise

# 认证路由（无需 token 验证）
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# 受保护的 API 父路由（所有业务接口需要 token 验证）
api_router = APIRouter(prefix="/api", dependencies=[Depends(verify_token)])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(configs.router, prefix="/configs", tags=["configs"])
api_router.include_router(modes.router, prefix="/modes", tags=["modes"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
app.include_router(api_router)





@app.get("/")
async def root():
    logger.debug("访问根路径")
    return {"message": "JobLens Web Manager API"}


@app.get("/health")
async def health():
    logger.debug("健康检查请求")
    return {"status": "healthy"}
