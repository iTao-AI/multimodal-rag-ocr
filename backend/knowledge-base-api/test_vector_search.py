#!/usr/bin/env python3
"""
向量检索优化测试脚本
测试混合检索、查询改写、重排序和缓存功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.bailian_config import config
from src.services.query_rewrite_service import QueryRewriteService
from src.services.rerank_service import RerankService
from src.utils.cache_manager import get_cache_manager


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置加载")
    print("=" * 60)
    
    try:
        config_dict = config.to_dict()
        print(f"✅ 配置加载成功")
        print(f"   嵌入模型：{config_dict['embedding']['model']}")
        print(f"   重排序模型：{config_dict['rerank']['model']}")
        print(f"   多模态模型：{config_dict['vl']['model']}")
        print(f"   混合检索 TopK: {config_dict['search_strategy']['hybrid_top_k']}")
        print(f"   最终 TopK: {config_dict['search_strategy']['final_top_k']}")
        print(f"   缓存启用：{config_dict['cache']['enabled']}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败：{e}")
        return False


def test_query_rewrite():
    """测试查询改写"""
    print("\n" + "=" * 60)
    print("测试 2: 查询改写")
    print("=" * 60)
    
    try:
        service = QueryRewriteService()
        query = "RAG 检索优化方法"
        
        print(f"原始查询：{query}")
        print("正在生成查询变体...")
        
        variations = service.rewrite_query(query, num_variations=3)
        print(f"✅ 生成 {len(variations)} 个变体:")
        for i, var in enumerate(variations, 1):
            print(f"   {i}. {var}")
        
        print("\n正在扩展查询...")
        expanded = service.expand_query(query, num_keywords=5)
        print(f"✅ 关键词：{expanded.get('keywords', [])}")
        
        return True
    except Exception as e:
        print(f"⚠️  查询改写测试失败（可能因为 API 调用）: {e}")
        return False


def test_rerank():
    """测试重排序"""
    print("\n" + "=" * 60)
    print("测试 3: 重排序")
    print("=" * 60)
    
    try:
        service = RerankService()
        query = "什么是 RAG"
        
        # 模拟文档
        documents = [
            {"id": "1", "text": "RAG 是检索增强生成的缩写，是一种结合检索和生成的 AI 技术"},
            {"id": "2", "text": "Python 是一种流行的编程语言，用于数据科学和 Web 开发"},
            {"id": "3", "text": "检索增强生成（RAG）通过检索外部知识来增强语言模型的回答能力"},
            {"id": "4", "text": "机器学习是人工智能的一个分支，研究如何让计算机从数据中学习"},
        ]
        
        print(f"查询：{query}")
        print(f"文档数量：{len(documents)}")
        print("正在重排序...")
        
        reranked = service.rerank(query, documents, top_n=3)
        print(f"✅ 重排序完成，返回 {len(reranked)} 个结果:")
        for i, doc in enumerate(reranked, 1):
            print(f"   {i}. [ID: {doc['id']}] 分数：{doc.get('rerank_score', 'N/A')}")
            print(f"      文本：{doc['text'][:50]}...")
        
        return True
    except Exception as e:
        print(f"⚠️  重排序测试失败（可能因为 API 调用）: {e}")
        return False


def test_cache():
    """测试缓存"""
    print("\n" + "=" * 60)
    print("测试 4: 缓存功能")
    print("=" * 60)
    
    try:
        cache = get_cache_manager()
        
        if not cache.enabled:
            print("⚠️  Redis 未启用，跳过缓存测试")
            print("   提示：启动 Redis: docker run -d --name redis -p 6379:6379 redis:latest")
            return True
        
        # 测试写入缓存
        test_data = [{"id": "1", "text": "测试数据"}]
        cache.set_query_result("test_query", test_data)
        print("✅ 写入缓存成功")
        
        # 测试读取缓存
        result = cache.get_query_result("test_query")
        if result:
            print("✅ 读取缓存成功")
            print(f"   数据：{result}")
        else:
            print("❌ 读取缓存失败")
            return False
        
        # 测试嵌入缓存
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        cache.set_embedding("test_text", test_embedding)
        emb_result = cache.get_embedding("test_text")
        if emb_result:
            print("✅ 嵌入向量缓存成功")
        
        # 获取统计信息
        stats = cache.get_statistics()
        print(f"✅ 缓存统计：{stats}")
        
        return True
    except Exception as e:
        print(f"❌ 缓存测试失败：{e}")
        return False


def test_hybrid_search():
    """测试混合检索"""
    print("\n" + "=" * 60)
    print("测试 5: 混合检索（BM25 + 向量）")
    print("=" * 60)
    
    try:
        from src.services.hybrid_search_service import HybridSearchService
        
        # 模拟文档
        documents = [
            {"id": "1", "text": "RAG 检索增强生成技术详解", "metadata": {}},
            {"id": "2", "text": "Python 编程从入门到精通", "metadata": {}},
            {"id": "3", "text": "向量数据库 Milvus 使用指南", "metadata": {}},
            {"id": "4", "text": "RAG 系统中的检索优化方法", "metadata": {}},
        ]
        
        query = "RAG 检索优化"
        print(f"查询：{query}")
        print(f"文档数量：{len(documents)}")
        
        # 注意：这里需要实际的向量服务，暂时跳过向量检索部分
        print("⚠️  混合检索需要集成实际的向量服务")
        print("   BM25 关键词检索已就绪")
        
        # 测试 BM25 分词
        service = HybridSearchService(vector_service=None)
        tokens = service._tokenize_chinese(query)
        print(f"✅ 中文分词：{tokens}")
        
        return True
    except Exception as e:
        print(f"❌ 混合检索测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🚀 向量检索优化功能测试")
    print("=" * 60)
    
    results = {
        "配置加载": test_config(),
        "查询改写": test_query_rewrite(),
        "重排序": test_rerank(),
        "缓存": test_cache(),
        "混合检索": test_hybrid_search(),
    }
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    print(f"\n总计：{total_passed}/{total_tests} 测试通过")
    
    if total_passed == total_tests:
        print("\n🎉 所有测试通过！系统已就绪。")
        return 0
    else:
        print("\n⚠️  部分测试未通过，请检查配置和依赖。")
        return 1


if __name__ == "__main__":
    exit(main())
