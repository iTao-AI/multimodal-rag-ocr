"""
Multimodal RAG Backend - Main Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chat.router import router as chat_router

app = FastAPI(
    title="Multimodal RAG API",
    description="多模态 RAG 系统 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "multimodal-rag"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
