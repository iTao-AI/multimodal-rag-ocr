"""
查询改写服务 - 使用 Qwen3.5-Plus 进行查询扩展和改写
"""
import logging
from typing import List, Dict, Any
import requests
import os

logger = logging.getLogger(__name__)


class QueryRewriteService:
    def __init__(self):
        """初始化查询改写服务"""
        self.api_key = os.getenv('RERANK_API_KEY', os.getenv('EMBEDDING_API_KEY'))
        self.api_url = os.getenv('RERANK_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model_name = os.getenv('RERANK_MODEL_NAME', 'qwen3.5-plus')
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def rewrite_query(self, query: str, num_variations: int = 3) -> List[str]:
        """
        改写查询，生成多个变体
        
        Args:
            query: 原始查询
            num_variations: 生成变体数量
            
        Returns:
            查询变体列表
        """
        prompt = f"""你是一个查询改写专家。请将以下用户查询改写成 {num_variations} 个不同的版本，保持语义相同但用词不同。

原始查询：{query}

请只返回改写后的查询，每行一个，不要编号，不要解释。"""
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': self.model_name,
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的查询改写助手。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 500
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            variations = result['choices'][0]['message']['content'].strip().split('\n')
            variations = [v.strip() for v in variations if v.strip()]
            
            # 确保包含原始查询
            if query not in variations:
                variations.insert(0, query)
            
            return variations[:num_variations + 1]
        except Exception as e:
            logger.error(f"查询改写失败：{e}")
            return [query]
    
    def expand_query(self, query: str, num_keywords: int = 5) -> Dict[str, Any]:
        """
        扩展查询，添加同义词和相关词
        
        Args:
            query: 原始查询
            num_keywords: 扩展关键词数量
            
        Returns:
            包含原始查询和扩展词的字典
        """
        prompt = f"""你是一个查询扩展专家。请为以下查询提取关键词，并为每个关键词提供 2-3 个同义词或相关词。

查询：{query}

请按以下 JSON 格式返回（只返回 JSON，不要其他内容）：
{{
    "original": "{query}",
    "keywords": ["关键词 1", "关键词 2", "关键词 3"],
    "synonyms": {{
        "关键词 1": ["同义词 1", "同义词 2"],
        "关键词 2": ["同义词 3", "同义词 4"]
    }}
}}"""
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': self.model_name,
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的查询扩展助手。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 500
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # 解析 JSON（简化处理，实际应该用 json.loads）
            import json
            try:
                expanded = json.loads(content)
                return expanded
            except:
                return {
                    'original': query,
                    'keywords': [query],
                    'synonyms': {}
                }
        except Exception as e:
            logger.error(f"查询扩展失败：{e}")
            return {
                'original': query,
                'keywords': [query],
                'synonyms': {}
            }
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """
        生成假设性答案（HyDE 策略）
        
        Args:
            query: 原始查询
            
        Returns:
            假设性答案文本
        """
        prompt = f"""请为以下问题生成一个简洁、准确的答案。这个答案将用于向量检索。

问题：{query}

要求：
- 答案长度控制在 100-200 字
- 包含关键信息和术语
- 直接回答问题，不要说"这个问题"等指代词"""
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    'model': self.model_name,
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的问答助手。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.5,
                    'max_tokens': 300
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            answer = result['choices'][0]['message']['content'].strip()
            return answer
        except Exception as e:
            logger.error(f"假设性答案生成失败：{e}")
            return query
