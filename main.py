from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import Base, engine
from backend.routers.core_router import router as core_router
from backend.routers.processing_router import router as processing_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="自闭症儿童干预IEP会议管理系统",
    description="全栈IEP会议纪要系统，支持音频转写、角色区分、AI摘要和加密邮件发送",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router)
app.include_router(processing_router)


@app.get("/")
async def root():
    return {
        "message": "IEP Meeting Management System API",
        "version": "1.0.0",
        "endpoints": {
            "core": "/api/core",
            "processing": "/api/processing"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
