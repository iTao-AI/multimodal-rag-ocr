from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from src.services.vector_service import VectorService
# 新增
from sys import path as sys_path
sys_path.append('/Users/mac/Developer/Projects/Active/multimodal-rag-ocr/backend/Database/milvus_server')
from intent_classifier import classify_intent
from hybrid_search import apply_trust_boost

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    use_rrf: bool = True  # 新增

class SearchResponse(BaseModel):
    id: str
    filename: str
    score: float
    intent: Optional[str] = None  # 新增
    is_verified: bool = False  # 新增

@router.post("/search", response_model=List[SearchResponse])
async def search_vectors(request: SearchRequest):
    try:
        # 1. 意图分类
        intent = classify_intent(request.query)

        # 2. 获取搜索参数
        # (可根据 intent 调整 top_k 等)

        # 3. 执行搜索
        results = VectorService.search(request.query, request.top_k)

        # 4. 可信提升
        verified_ids = set(os.environ.get('VERIFIED_FILE_IDS', '').split(',') if os.environ.get('VERIFIED_FILE_IDS') else [])
        results = apply_trust_boost(results, verified_ids)

        # 5. 构建响应
        return [SearchResponse(
            id=r.get('id', ''),
            filename=r.get('filename', ''),
            score=r.get('score', 0),
            intent=intent,
            is_verified=r.get('is_verified', False)
        ) for r in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
