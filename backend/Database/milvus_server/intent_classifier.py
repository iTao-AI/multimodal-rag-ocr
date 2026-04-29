"""零延迟启发式意图分类器 — 通过正则匹配检测查询意图，0ms 延迟"""
import re
from typing import Literal

QueryIntent = Literal["entity", "temporal", "technical", "general"]

ENTITY_PATTERNS = [
    r"什么是.*", r"谁.*", r".*是什么", r".*介绍一下",
    r"what\s+is", r"who\s+is", r"tell\s+me\s+about",
]
TEMPORAL_PATTERNS = [
    r".*什么时候.*", r".*何时.*", r".*历史.*", r".*版本.*",
    r"when\s+", r"history", r"version\s+",
]
TECHNICAL_PATTERNS = [
    r".*代码.*", r".*实现.*", r".*怎么用.*", r".*配置.*",
    r"how\s+to", r"code", r"implement", r"config",
]

def classify_intent(query: str) -> QueryIntent:
    q = query.lower()
    for pattern in TECHNICAL_PATTERNS:
        if re.search(pattern, q):
            return "technical"
    for pattern in TEMPORAL_PATTERNS:
        if re.search(pattern, q):
            return "temporal"
    for pattern in ENTITY_PATTERNS:
        if re.search(pattern, q):
            return "entity"
    return "general"

def get_search_params_by_intent(intent: QueryIntent) -> dict:
    params = {"top_k": 10, "bm25_weight": 0.3, "vector_weight": 0.7}
    if intent == "technical":
        params["bm25_weight"] = 0.5
        params["vector_weight"] = 0.5
        params["top_k"] = 15
    elif intent == "entity":
        params["bm25_weight"] = 0.2
        params["vector_weight"] = 0.8
    elif intent == "temporal":
        params["top_k"] = 20
    return params
