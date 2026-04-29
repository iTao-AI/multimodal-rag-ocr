"""意图分类器单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from intent_classifier import classify_intent, get_search_params_by_intent


def test_chinese_entity():
    assert classify_intent("什么是大语言模型") == "entity"
    assert classify_intent("介绍一下 RAG 技术") == "entity"
    assert classify_intent("向量数据库是什么") == "entity"


def test_chinese_temporal():
    assert classify_intent("什么时候发布的 GPT-4") == "temporal"
    assert classify_intent("这个项目的历史") == "temporal"
    assert classify_intent("有哪些版本") == "temporal"


def test_chinese_technical():
    assert classify_intent("怎么用 Milvus 做向量检索") == "technical"
    assert classify_intent("BM25 的代码实现") == "technical"
    assert classify_intent("如何配置混合检索") == "technical"


def test_chinese_general():
    assert classify_intent("今天天气怎么样") == "general"
    assert classify_intent("你好") == "general"


def test_english_entity():
    assert classify_intent("What is a vector database") == "entity"
    assert classify_intent("who is the creator of Python") == "entity"


def test_english_temporal():
    assert classify_intent("when was Milvus released") == "temporal"
    assert classify_intent("history of RAG") == "temporal"


def test_english_technical():
    assert classify_intent("how to implement BM25") == "technical"
    assert classify_intent("config file for Milvus") == "technical"


def test_search_params_technical():
    params = get_search_params_by_intent("technical")
    assert params["bm25_weight"] == 0.5
    assert params["vector_weight"] == 0.5
    assert params["top_k"] == 15


def test_search_params_entity():
    params = get_search_params_by_intent("entity")
    assert params["bm25_weight"] == 0.2
    assert params["vector_weight"] == 0.8
    assert params["top_k"] == 10


def test_search_params_temporal():
    params = get_search_params_by_intent("temporal")
    assert params["top_k"] == 20


def test_search_params_general():
    params = get_search_params_by_intent("general")
    assert params["top_k"] == 10
    assert params["bm25_weight"] == 0.3
    assert params["vector_weight"] == 0.7


if __name__ == "__main__":
    test_chinese_entity()
    test_chinese_temporal()
    test_chinese_technical()
    test_chinese_general()
    test_english_entity()
    test_english_temporal()
    test_english_technical()
    test_search_params_technical()
    test_search_params_entity()
    test_search_params_temporal()
    test_search_params_general()
    print("✅ All intent classifier tests passed!")
