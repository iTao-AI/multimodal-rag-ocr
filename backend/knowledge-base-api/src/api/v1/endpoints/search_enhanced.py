"""
增强的搜索 API - 支持混合检索、查询改写和重排序
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os

from src.services.hybrid_search_service import HybridSearchService
from src.services.query_rewrite_service import QueryRewriteService
from src.services.rerank_service import RerankService
from src.utils.cache_manager import get_cache_manager, CacheManager
from src.core.bailian_config import config

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    use_rewrite: bool = True
    use_rerank: bool = True
    use_cache: bool = True


class SearchResult(BaseModel):
    id: str
    text: str
    filename: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query_used: str
    rewrite_applied: bool = False
    rerank_applied: bool = False
    cache_hit: bool = False
    total_results: int


@router.post("/search", response_model=SearchResponse)
async def search_enhanced(
    request: SearchRequest,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """
    增强的搜索接口
    
    功能：
    1. 查询缓存检查
    2. 查询改写（可选）
    3. 混合检索（向量 + BM25）
    4. LLM 重排序（可选）
    5. 结果缓存
    """
    try:
        # 1. 检查缓存
        if request.use_cache:
            cached_results = cache_manager.get_query_result(request.query)
            if cached_results:
                logger.info(f"缓存命中：{request.query}")
                return SearchResponse(
                    results=cached_results,
                    query_used=request.query,
                    cache_hit=True
                )
        
        # 2. 查询改写
        query_to_use = request.query
        rewrite_applied = False
        
        if request.use_rewrite:
            rewrite_service = QueryRewriteService()
            variations = rewrite_service.rewrite_query(request.query, num_variations=2)
            # 使用第一个变体（通常是原始查询 + 最佳改写）
            query_to_use = variations[0]
            rewrite_applied = query_to_use != request.query
            logger.info(f"查询改写：{request.query} -> {query_to_use}")
        
        # 3. 混合检索
        # 注意：这里需要集成到现有的 VectorService
        # 暂时使用简化版本
        hybrid_service = HybridSearchService(
            vector_service=None,  # 需要注入实际的向量服务
            bm25_weight=config.BM25_WEIGHT,
            vector_weight=config.VECTOR_WEIGHT,
            top_k=config.HYBRID_SEARCH_TOP_K,
            final_top_k=request.top_k * 2  # 重排序前返回更多结果
        )
        
        # 获取文档（这里需要从实际的数据源获取）
        # TODO: 集成到实际的文档检索流程
        documents = []  # 占位符
        
        # 4. 重排序
        rerank_applied = False
        if request.use_rerank and len(documents) > request.top_k:
            rerank_service = RerankService()
            documents = rerank_service.rerank(
                query=query_to_use,
                documents=documents,
                top_n=request.top_k
            )
            rerank_applied = True
        
        # 5. 格式化结果
        results = []
        for doc in documents[:request.top_k]:
            results.append(SearchResult(
                id=doc.get('id', ''),
                text=doc.get('text', ''),
                filename=doc.get('filename', ''),
                score=doc.get('hybrid_score', doc.get('rerank_score', 0.0)),
                metadata=doc.get('metadata')
            ))
        
        # 6. 缓存结果
        if request.use_cache and results:
            cache_manager.set_query_result(
                request.query,
                [r.model_dump() for r in results]
            )
        
        return SearchResponse(
            results=results,
            query_used=query_to_use,
            rewrite_applied=rewrite_applied,
            rerank_applied=rerank_applied,
            cache_hit=False,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"搜索失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索失败：{str(e)}")


@router.get("/search/stats")
async def get_search_stats(cache_manager: CacheManager = Depends(get_cache_manager)):
    """获取搜索统计信息"""
    stats = {
        'cache': cache_manager.get_statistics(),
        'config': config.to_dict()
    }
    return stats
