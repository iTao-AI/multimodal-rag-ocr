"""
查询改写服务 - 使用 LLM 进行查询扩展和改写
从原始 Multimodal_RAG 项目适配

功能:
- rewrite_query: 生成语义相同的查询变体
- expand_query: 提取关键词并扩展同义词
- generate_hypothetical_answer: HyDE 策略，生成假设性答案

失败时降级到原始查询，不影响现有链路。
"""
import json
import os
from typing import List, Dict, Any

import httpx

# 复用 kb_chat.py 中已有的 LLM 配置
LLM_API_URL = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_API_KEY = os.getenv("API_KEY", "")
LLM_MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-vl-plus")

# 查询改写特定配置
QUERY_REWRITE_VARIATIONS = int(os.getenv("QUERY_REWRITE_VARIATIONS", "3"))


class QueryRewriteService:
    def __init__(
        self,
        api_url: str = LLM_API_URL,
        api_key: str = LLM_API_KEY,
        model_name: str = LLM_MODEL_NAME,
        num_variations: int = QUERY_REWRITE_VARIATIONS,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.num_variations = num_variations

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def rewrite_query(self, query: str) -> List[str]:
        """
        改写查询，生成多个语义相同的变体

        Args:
            query: 原始查询

        Returns:
            查询变体列表（包含原始查询）
        """
        prompt = f"""你是一个查询改写专家。请将以下用户查询改写成 {self.num_variations} 个不同的版本，保持语义相同但用词不同。

原始查询：{query}

请只返回改写后的查询，每行一个，不要编号，不要解释。"""

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的查询改写助手。"},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                result = response.json()

                variations = result["choices"][0]["message"]["content"].strip().split("\n")
                variations = [v.strip() for v in variations if v.strip()]

                # 确保包含原始查询
                if query not in variations:
                    variations.insert(0, query)

                return variations[: self.num_variations + 1]

        except Exception as e:
            print(f"查询改写失败，降级到原始查询: {e}")
            return [query]

    async def expand_query(self, query: str, num_keywords: int = 5) -> Dict[str, Any]:
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
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "synonyms": {{
        "关键词1": ["同义词1", "同义词2"],
        "关键词2": ["同义词3", "同义词4"]
    }}
}}"""

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的查询扩展助手。"},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"original": query, "keywords": [query], "synonyms": {}}

        except Exception as e:
            print(f"查询扩展失败: {e}")
            return {"original": query, "keywords": [query], "synonyms": {}}

    async def generate_hypothetical_answer(self, query: str) -> str:
        """
        生成假设性答案（HyDE 策略）
        用一个假设的答案去检索，提高召回质量

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
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的问答助手。"},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.5,
                        "max_tokens": 300,
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"假设性答案生成失败: {e}")
            return query


# 全局单例
_query_rewrite_service = None


def get_query_rewrite_service() -> QueryRewriteService:
    global _query_rewrite_service
    if _query_rewrite_service is None:
        _query_rewrite_service = QueryRewriteService()
    return _query_rewrite_service
