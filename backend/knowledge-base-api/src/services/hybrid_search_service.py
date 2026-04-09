"""
混合检索服务 - 结合向量检索和 BM25 关键词检索
"""
import logging
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import jieba.analyse

logger = logging.getLogger(__name__)


class HybridSearchService:
    def __init__(
        self,
        vector_service,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        top_k: int = 50,
        final_top_k: int = 10
    ):
        """
        初始化混合检索服务
        
        Args:
            vector_service: 向量检索服务实例
            bm25_weight: BM25 权重
            vector_weight: 向量检索权重
            top_k: 初筛返回数量
            final_top_k: 最终返回数量
        """
        self.vector_service = vector_service
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.top_k = top_k
        self.final_top_k = final_top_k
        
        # 中文停用词（简化版）
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这'
        ])
    
    def _tokenize_chinese(self, text: str) -> List[str]:
        """中文分词"""
        words = jieba.lcut(text.lower())
        return [w for w in words if w not in self.stopwords and len(w.strip()) > 0]
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """归一化分数到 0-1 范围"""
        if not scores:
            return scores
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [0.5] * len(scores)
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def search(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档包含 'text', 'vector', 'metadata' 等字段
            
        Returns:
            排序后的文档列表
        """
        if not documents:
            return []
        
        # 1. 向量检索分数
        vector_scores = self._get_vector_scores(query, documents)
        
        # 2. BM25 关键词检索分数
        bm25_scores = self._get_bm25_scores(query, documents)
        
        # 3. 归一化分数
        vector_scores_norm = self._normalize_scores(vector_scores)
        bm25_scores_norm = self._normalize_scores(bm25_scores)
        
        # 4. 加权融合
        final_scores = []
        for i, doc in enumerate(documents):
            score = (
                self.vector_weight * vector_scores_norm[i] +
                self.bm25_weight * bm25_scores_norm[i]
            )
            doc['hybrid_score'] = score
            final_scores.append(score)
        
        # 5. 按分数排序
        scored_docs = list(zip(documents, final_scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 6. 返回 top_k
        return [doc for doc, score in scored_docs[:self.final_top_k]]
    
    def _get_vector_scores(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """获取向量检索分数"""
        try:
            # 调用向量服务获取查询向量并检索
            query_vector = self.vector_service.get_query_vector(query)
            results = self.vector_service.search_by_vector(query_vector, self.top_k)
            
            # 构建文档 ID 到分数的映射
            score_map = {}
            for result in results:
                doc_id = result.get('id') or result.get('doc_id')
                score = result.get('score', 0)
                if doc_id:
                    score_map[doc_id] = score
            
            # 为每个文档分配分数
            scores = []
            for doc in documents:
                doc_id = doc.get('id') or doc.get('doc_id')
                scores.append(score_map.get(doc_id, 0))
            
            return scores
        except Exception as e:
            logger.error(f"向量检索失败：{e}")
            return [0.0] * len(documents)
    
    def _get_bm25_scores(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """获取 BM25 关键词检索分数"""
        try:
            # 准备语料库
            corpus = [self._tokenize_chinese(doc.get('text', '')) for doc in documents]
            query_tokens = self._tokenize_chinese(query)
            
            # 初始化 BM25
            bm25 = BM25Okapi(corpus)
            
            # 计算分数
            scores = bm25.get_scores(query_tokens)
            return scores.tolist() if hasattr(scores, 'tolist') else list(scores)
        except Exception as e:
            logger.error(f"BM25 检索失败：{e}")
            return [0.0] * len(documents)
