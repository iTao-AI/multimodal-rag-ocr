"""
重排序服务 - 使用 Qwen3.5-Plus 对检索结果进行精排
"""
import logging
from typing import List, Dict, Any
import requests
import os

logger = logging.getLogger(__name__)


class RerankService:
    def __init__(self):
        """初始化重排序服务"""
        self.api_key = os.getenv('RERANK_API_KEY', os.getenv('EMBEDDING_API_KEY'))
        self.api_url = os.getenv('RERANK_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model_name = os.getenv('RERANK_MODEL_NAME', 'qwen3.5-plus')
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表，每个文档包含 'text' 和 'metadata'
            top_n: 返回前 N 个结果
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        # 如果文档数量少，直接返回
        if len(documents) <= top_n:
            return documents
        
        try:
            # 构建提示词
            prompt = self._build_rerank_prompt(query, documents)
            
            # 调用 Qwen 进行重排序
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': self.model_name,
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的文档重排序助手。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.1,
                    'max_tokens': 1000
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            ranked_indices = self._parse_rerank_result(
                result['choices'][0]['message']['content'],
                len(documents)
            )
            
            # 按排序结果返回文档
            reranked_docs = []
            for idx in ranked_indices[:top_n]:
                if 0 <= idx < len(documents):
                    doc = documents[idx].copy()
                    doc['rerank_score'] = len(ranked_indices) - ranked_indices.index(idx)
                    reranked_docs.append(doc)
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"重排序失败：{e}")
            # 降级：返回原始文档
            return documents[:top_n]
    
    def _build_rerank_prompt(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """构建重排序提示词"""
        doc_texts = []
        for i, doc in enumerate(documents):
            text = doc.get('text', '')[:500]  # 限制长度
            doc_texts.append(f"文档 {i}: {text}")
        
        prompt = f"""请根据以下查询，对文档进行相关性排序（从最相关到最不相关）。

查询：{query}

文档列表：
{chr(10).join(doc_texts)}

请只返回排序后的文档编号列表，用逗号分隔，例如：2,0,3,1
不要解释，不要其他内容。"""
        
        return prompt
    
    def _parse_rerank_result(self, result_text: str, num_docs: int) -> List[int]:
        """解析重排序结果"""
        try:
            # 提取数字
            import re
            indices = re.findall(r'\d+', result_text)
            indices = [int(i) for i in indices if 0 <= int(i) < num_docs]
            
            # 去重
            seen = set()
            unique_indices = []
            for i in indices:
                if i not in seen:
                    seen.add(i)
                    unique_indices.append(i)
            
            # 补充缺失的索引
            all_indices = set(range(num_docs))
            missing = list(all_indices - set(unique_indices))
            unique_indices.extend(missing)
            
            return unique_indices
        except Exception as e:
            logger.error(f"解析重排序结果失败：{e}")
            return list(range(num_docs))
    
    def score_relevance(
        self,
        query: str,
        document: str,
        max_score: float = 1.0
    ) -> float:
        """
        对单个文档进行相关性打分
        
        Args:
            query: 查询文本
            document: 文档文本
            max_score: 最大分数
            
        Returns:
            相关性分数
        """
        prompt = f"""请评估以下文档与查询的相关性，打分 0-1 分（保留 2 位小数）。

查询：{query}

文档：{document[:1000]}

请只返回一个数字，例如：0.85"""
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': self.model_name,
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的文档相关性评估助手。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.1,
                    'max_tokens': 50
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            score_text = result['choices'][0]['message']['content'].strip()
            
            # 提取数字
            import re
            match = re.search(r'(\d+\.?\d*)', score_text)
            if match:
                score = float(match.group(1))
                return min(score, max_score)
            else:
                return max_score / 2
                
        except Exception as e:
            logger.error(f"相关性打分失败：{e}")
            return max_score / 2
