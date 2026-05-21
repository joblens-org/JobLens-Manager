from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routers import services, jobs, metrics, configs, modes, roles, rules, clusters
from contextlib import asynccontextmanager
from backend.common.logger import logger
from backend.common import initialize_etcd
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

app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(configs.router, prefix="/api/configs", tags=["configs"])
app.include_router(modes.router, prefix="/api/modes", tags=["modes"])
app.include_router(roles.router, prefix="/api/roles", tags=["roles"])
app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
app.include_router(clusters.router, prefix="/api/clusters", tags=["clusters"])





@app.get("/")
async def root():
    logger.debug("访问根路径")
    return {"message": "JobLens Web Manager API"}


@app.get("/health")
async def health():
    logger.debug("健康检查请求")
    return {"status": "healthy"}
