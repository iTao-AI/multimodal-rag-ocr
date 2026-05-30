import uuid
import logging
import json
import os
import requests
import time
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from dotenv import load_dotenv

# 加载 backend/.env 文件
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)

# 环境变量配置
MILVUS_HOST = os.getenv("MILVUS_HOST")
MILVUS_PORT = os.getenv("MILVUS_PORT")
EMBEDDING_URL = os.getenv("EMBEDDING_URL")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")

# Pydantic 模型定义
class DocumentChunk(BaseModel):
    chunk_text: str
    filename: str
    file_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}

class UploadKBRequest(BaseModel):
    collection_name: str
    file_data: Dict[str, Any]

class UploadResponse(BaseModel):
    filename: str
    file_id: str
    status: str
    message: str
    chunks_count: int = 0

class SearchRequest(BaseModel):
    collection_name: str
    query_text: str
    top_k: int = 10
    filter_expr: Optional[str] = None

class SearchByFilenameRequest(BaseModel):
    collection_name: str
    filename: str
    top_k: int = 10

class DeleteRequest(BaseModel):
    collection_name: str
    filename: str

class DeleteKBRequest(BaseModel):
    collection_name: str


# 初始化结构化日志
try:
    from common.logging_config import setup_logging
    setup_logging("rag-milvus")
except Exception:
    pass

def call_with_retry(func, max_retries=3, base_delay=1):
    """
    带指数退避重试的函数包装器
    重试间隔：base_delay * 2^(attempt-1)，即 1s → 2s → 4s
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # 最后一次，重新抛出
            delay = base_delay * (2 ** attempt)
            logger.info("API 调用失败 (第 %d/%d 次重试): %s，%ds 后重试", attempt + 1, max_retries, e, delay)
            time.sleep(delay)


class MilvusRAGService:
    def __init__(self):
        self.milvus_host = MILVUS_HOST
        self.milvus_port = MILVUS_PORT
        self.embedding_url = EMBEDDING_URL
        self.embedding_model_name = EMBEDDING_MODEL_NAME
        self.embedding_api_key = EMBEDDING_API_KEY
        
        logger.info("Milvus配置: %s:%s", self.milvus_host, self.milvus_port)
        logger.info("Embedding配置: URL=%s, Model=%s", self.embedding_url, self.embedding_model_name)
        
        self.connect_to_milvus()
    
    def connect_to_milvus(self):
        """连接到Milvus服务"""
        try:
            connections.connect(
                "default", 
                host=self.milvus_host, 
                port=self.milvus_port
            )
            logger.info("Successfully connected to Milvus at %s:%s", self.milvus_host, self.milvus_port)
        except Exception as e:
            logger.error("Failed to connect to Milvus: %s", e)
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """单个文本生成向量（用于query）"""
        def _call_api():
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.embedding_api_key}"
            }

            payload = {
                "model": self.embedding_model_name,
                "input": [text]
            }

            response = requests.post(self.embedding_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                result = response.json()
                embedding = result["data"][0]["embedding"]
                return embedding
            else:
                raise Exception(f"Embedding API 返回错误: {response.status_code}")

        try:
            return call_with_retry(_call_api, max_retries=3, base_delay=1)
        except Exception as e:
            logger.error("Embedding generation failed after retries: %s", e)
            raise HTTPException(
                status_code=503,
                detail=f"向量生成服务不可用: {e}"
            )
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        批量生成embeddings，使用线程池并行处理多个批次
        
        Args:
            texts: 文本列表
            batch_size: 每批次处理的文本数量
        
        Returns:
            按顺序返回的embedding列表
        """
        if not texts:
            return []
        
        total_texts = len(texts)
        logger.info("开始批量生成 %d 个文本的embeddings，批次大小: %d", total_texts, batch_size)
        
        # 预分配结果列表
        all_embeddings = [None] * total_texts
        start_time = time.time()
        
        def process_batch(batch_idx: int, batch_texts: List[str]) -> tuple:
            """处理单个批次"""
            start_idx = batch_idx * batch_size
            
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.embedding_api_key}"
                }
                
                payload = {
                    "model": self.embedding_model_name,
                    "input": batch_texts
                }
                
                response = requests.post(
                    self.embedding_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    batch_embeddings = [item["embedding"] for item in result["data"]]
                    return batch_idx, start_idx, batch_embeddings, None
                else:
                    error_msg = f"API返回错误: {response.status_code}"
                    logger.warning("批次 %d %s", batch_idx + 1, error_msg)
                    fallback_dim = self.get_model_dimension(self.embedding_model_name)
                    batch_embeddings = [np.random.rand(fallback_dim).tolist() for _ in batch_texts]
                    return batch_idx, start_idx, batch_embeddings, error_msg
                    
            except Exception as e:
                error_msg = f"处理异常: {str(e)}"
                logger.warning("批次 %d %s", batch_idx + 1, error_msg)
                fallback_dim = self.get_model_dimension(self.embedding_model_name)
                batch_embeddings = [np.random.rand(fallback_dim).tolist() for _ in batch_texts]
                return batch_idx, start_idx, batch_embeddings, error_msg
        
        # 准备批次
        batches = []
        for i in range(0, total_texts, batch_size):
            batch_end = min(i + batch_size, total_texts)
            batches.append((i // batch_size, texts[i:batch_end]))
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_batch = {
                executor.submit(process_batch, batch_idx, batch_texts): batch_idx
                for batch_idx, batch_texts in batches
            }
            
            for future in as_completed(future_to_batch):
                batch_idx, start_idx, batch_embeddings, error = future.result()
                
                # 填充结果
                for i, embedding in enumerate(batch_embeddings):
                    all_embeddings[start_idx + i] = embedding
        
        elapsed = time.time() - start_time
        rate = total_texts / elapsed if elapsed > 0 else 0
        logger.info("批量生成完成，总耗时: %.2f秒，平均速率: %.2f 文本/秒", elapsed, rate)
        
        return all_embeddings
    
    def get_model_dimension(self, model_name: str) -> int:
        """获取模型的向量维度"""
        model_dimensions = {
            "jina-embeddings-v4": 2048,
            "jina-embeddings-v3": 1024,
            "jina-embeddings-v2-base-zh": 512,
            "text-embedding-ada-002": 1536,
            "text-embedding-v4": 1024
        }
        return model_dimensions.get(model_name, 1024)
    
    def create_collection_schema(self, embedding_dim: int = 1024) -> CollectionSchema:
        """创建Collection的Schema"""
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="file_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="RAG Knowledge Base Collection"
        )
        return schema
    
    def generate_collection_id(self) -> str:
        """生成符合Milvus规范的collection ID"""
        import time
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        return f"kb_{timestamp}"

    def save_name_mapping(self, collection_id: str, display_name: str):
        """保存collection ID和显示名称的映射关系到JSON文件"""
        import json
        from pathlib import Path

        # 映射文件路径
        mapping_file = Path(__file__).parent / "collection_name_mapping.json"

        # 读取现有映射
        mappings = {}
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mappings = json.load(f)

        # 更新映射
        mappings[collection_id] = {
            "display_name": display_name,
            "created_at": datetime.now().isoformat()
        }

        # 保存映射
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)

        logger.info("Saved mapping: %s -> %s", collection_id, display_name)

    def get_name_mapping(self, collection_id: str = None) -> Dict[str, Any]:
        """获取名称映射"""
        import json
        from pathlib import Path

        mapping_file = Path(__file__).parent / "collection_name_mapping.json"

        if not mapping_file.exists():
            return {}

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        if collection_id:
            return mappings.get(collection_id, {})
        return mappings

    def delete_name_mapping(self, collection_id: str):
        """删除名称映射"""
        import json
        from pathlib import Path

        mapping_file = Path(__file__).parent / "collection_name_mapping.json"

        if not mapping_file.exists():
            return

        with open(mapping_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)

        if collection_id in mappings:
            del mappings[collection_id]

            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)

            logger.info("Deleted mapping: %s", collection_id)

    def create_knowledge_base(self, display_name: str, embedding_dim: int = None) -> tuple:
        """
        创建知识库（Collection）

        Args:
            display_name: 用户输入的显示名称（可以是中文）
            embedding_dim: embedding维度

        Returns:
            (collection_id, success): 返回collection ID和是否成功
        """
        try:
            # 生成符合Milvus规范的collection ID
            collection_id = self.generate_collection_id()

            if utility.has_collection(collection_id):
                # 理论上不会发生，因为使用时间戳
                collection_id = self.generate_collection_id()

            if embedding_dim is None:
                embedding_dim = self.get_model_dimension(self.embedding_model_name)

            schema = self.create_collection_schema(embedding_dim)
            collection = Collection(name=collection_id, schema=schema)

            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)

            # 参考milvus_kb_service: 创建后立即加载collection
            collection.load()

            # 保存名称映射
            self.save_name_mapping(collection_id, display_name)

            logger.info("Created knowledge base: %s ('%s') with embedding_dim: %s", collection_id, display_name, embedding_dim)
            return collection_id, True

        except Exception as e:
            logger.error("Failed to create knowledge base: %s", e)
            raise
    
    def delete_knowledge_base(self, collection_id: str) -> bool:
        """删除知识库"""
        try:
            if utility.has_collection(collection_id):
                utility.drop_collection(collection_id)
                # 同时删除名称映射
                self.delete_name_mapping(collection_id)
                logger.info("Deleted knowledge base: %s", collection_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete knowledge base: %s", e)
            raise
    
    def create_or_get_collection(self, collection_name: str, embedding_dim: int = None) -> Collection:
        """创建或获取Collection"""
        if utility.has_collection(collection_name):
            collection = Collection(collection_name)
            # 确保已加载
            try:
                collection.load()
            except Exception as e:
                logger.error("加载已存在的collection时出错: %s", e)
        else:
            if embedding_dim is None:
                embedding_dim = self.get_model_dimension(self.embedding_model_name)
                
            schema = self.create_collection_schema(embedding_dim)
            collection = Collection(name=collection_name, schema=schema)
            
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            # 参考milvus_kb_service: 创建后立即加载
            collection.load()
        
        return collection
    
    def parse_json_file(self, json_data: Dict[str, Any]) -> List[DocumentChunk]:
        """解析JSON文件并转换为DocumentChunk列表"""
        try:
            documents = []
            
            # 提取基本信息
            filename = json_data.get("filename", "unknown.txt")
            if filename.startswith("/"):
                filename = os.path.basename(filename)
            
            data_section = json_data.get("data", {})
            chunks = data_section.get("chunks", [])
                        
            # 为每个chunk创建DocumentChunk
            for i, chunk in enumerate(chunks):
                chunk_text = chunk.get("text", "")
                if not chunk_text.strip():
                    logger.warning("跳过空chunk %d", i)
                    continue
                
                # 构建metadata
                metadata = {
                    "page_start": chunk.get("page_start", 1),
                    "page_end": chunk.get("page_end", 1),
                    "pages": chunk.get("pages", [1]),
                    "text_length": chunk.get("text_length", len(chunk_text)),
                    "continued": chunk.get("continued", False),
                    "cross_page_bridge": chunk.get("cross_page_bridge", False),
                    "is_table_like": chunk.get("is_table_like", False),
                    "chunk_index": i
                }
                
                # 添加文档级别的metadata
                if "metadata" in data_section:
                    metadata.update(data_section["metadata"])
                
                doc = DocumentChunk(
                    chunk_text=chunk_text,
                    filename=filename,
                    file_id=str(uuid.uuid4()),
                    metadata=metadata
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error("Failed to parse JSON file: %s", e)
            raise HTTPException(status_code=400, detail=f"JSON解析失败: {str(e)}")
    
    def insert_documents(self, collection_name: str, documents: List[DocumentChunk]) -> List[str]:
        """
        批量插入文档到Collection
        参考milvus_kb_service.py的操作方式
        """
        if not documents:
            return []
        
        try:
            # 准备数据
            logger.info("准备 %d 个文档数据", len(documents))
            
            chunk_texts = []
            filenames = []
            file_ids = []
            metadatas = []
            
            for doc in documents:
                chunk_texts.append(doc.chunk_text)
                filenames.append(doc.filename)
                file_ids.append(doc.file_id or str(uuid.uuid4()))
                metadatas.append(json.dumps(doc.metadata, ensure_ascii=False))
            
            # 批量生成embeddings
            logger.info("批量生成embeddings")
            EMBED_BATCH_SIZE = 32
            embeddings = self.generate_embeddings_batch(chunk_texts, batch_size=EMBED_BATCH_SIZE)
            
            # 检测embedding维度
            embedding_dim = len(embeddings[0])
            logger.info("检测到embedding维度: %d", embedding_dim)
            
            # 创建或获取collection（会自动load）
            collection = self.create_or_get_collection(collection_name, embedding_dim)
            
            # 分批插入Milvus
            logger.info("分批插入Milvus")
            MILVUS_BATCH_SIZE = 1000
            total_docs = len(documents)
            
            current_time = datetime.now().isoformat()
            
            for i in range(0, total_docs, MILVUS_BATCH_SIZE):
                end_idx = min(i + MILVUS_BATCH_SIZE, total_docs)
                
                # 准备当前批次数据 - 参考milvus_kb_service.py的entities格式
                entities = [
                    chunk_texts[i:end_idx],
                    filenames[i:end_idx],
                    file_ids[i:end_idx],
                    embeddings[i:end_idx],
                    metadatas[i:end_idx],
                    [current_time] * (end_idx - i)
                ]
                
                # 插入 - 参考milvus_kb_service.py，不调用flush
                collection.insert(entities)
            
            logger.info("插入完成，共 %d 条文档", len(file_ids))
            
            # 插入完成后，确保collection保持加载状态（虽然理论上已经加载）
            try:
                if not collection.has_index():
                    collection.load()
                    logger.info("插入后重新加载collection")
            except Exception as load_err:
                logger.warning("插入后加载collection警告: %s", load_err)
            
            return file_ids
            
        except Exception as e:
            logger.error("插入文档失败: %s", e)
            raise HTTPException(status_code=500, detail=f"插入文档失败: {str(e)}")
    
    def search_by_text(self, collection_name: str, query_text: str, 
                      top_k: int = 10, filter_expr: Optional[str] = None) -> List[Dict]:
        """根据文本搜索相似文档"""
        try:
            if not utility.has_collection(collection_name):
                raise HTTPException(status_code=404, detail=f"知识库 {collection_name} 不存在")
            
            # 生成查询向量
            logger.info("为查询文本生成embedding: %s...", query_text[:50])
            query_embedding = self.generate_embedding(query_text)
            
            collection = Collection(collection_name)
            
            # 参考milvus_kb_service: 确保collection已加载
            try:
                # 检查collection是否有索引（间接判断是否需要load）
                if not collection.has_index():
                    logger.info("Collection '%s' 没有索引，正在加载...", collection_name)
                    collection.load()
                else:
                    # 即使有索引，也尝试load以确保在内存中
                    collection.load()
                logger.info("Collection '%s' 已确保加载", collection_name)
            except Exception as load_err:
                logger.error("加载collection时出错: %s", load_err)
                # 尝试继续，可能已经加载
            
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            output_fields = ["chunk_text", "filename", "file_id", "metadata", "created_at"]
            
            logger.info("执行向量搜索，top_k: %d", top_k)
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields
            )
            
            # 格式化结果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        "id": hit.id,
                        "score": hit.score,
                        "chunk_text": hit.entity.get("chunk_text"),
                        "filename": hit.entity.get("filename"),
                        "file_id": hit.entity.get("file_id"),
                        "metadata": json.loads(hit.entity.get("metadata", "{}")),
                        "created_at": hit.entity.get("created_at")
                    }
                    formatted_results.append(result)
            
            logger.info("搜索完成，找到 %d 个结果", len(formatted_results))
            return formatted_results
            
        except Exception as e:
            logger.error("搜索失败: %s", e)
            import traceback
            logger.error("详细错误: %s", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
    
    def search_by_filename(self, collection_name: str, filename: str, top_k: int = 10) -> List[Dict]:
        """根据文件名检索知识库内信息"""
        try:
            if not utility.has_collection(collection_name):
                raise HTTPException(status_code=404, detail=f"知识库 {collection_name} 不存在")
            
            collection = Collection(collection_name)
            
            # 确保collection已加载
            try:
                collection.load()
                logger.info("Collection '%s' 已加载", collection_name)
            except Exception as load_err:
                logger.warning("加载collection警告: %s", load_err)
            
            # 构建查询表达式
            expr = f'filename == "{filename}"'
            logger.info("根据文件名查询: %s", expr)
            
            # 执行查询
            results = collection.query(
                expr=expr,
                output_fields=["chunk_text", "filename", "file_id", "metadata", "created_at"]
            )
            results = results[:top_k]

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result.get("id"),
                    "chunk_text": result.get("chunk_text"),
                    "filename": result.get("filename"),
                    "file_id": result.get("file_id"),
                    "metadata": json.loads(result.get("metadata", "{}")),
                    "created_at": result.get("created_at")
                }
                formatted_results.append(formatted_result)
            
            logger.info("根据文件名 %s 找到 %d 个结果", filename, len(formatted_results))
            return formatted_results
            
        except Exception as e:
            logger.error("根据文件名检索失败: %s", e)
            import traceback
            logger.error("详细错误: %s", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"根据文件名检索失败: {str(e)}")
    
    def delete_documents_by_filename(self, collection_name: str, filename: str) -> int:
        """根据文件名删除文档"""
        try:
            if not utility.has_collection(collection_name):
                raise HTTPException(status_code=404, detail=f"知识库 {collection_name} 不存在")
            
            collection = Collection(collection_name)
            
            # 删除前确保collection已加载
            try:
                collection.load()
            except Exception as load_err:
                logger.warning("加载collection警告: %s", load_err)
            
            # 构建删除表达式
            expr = f'filename == "{filename}"'
            logger.info("删除文件: %s", expr)
            
            # 执行删除 - 参考milvus_kb_service.py，不调用flush
            collection.delete(expr)
            
            logger.info("删除文件 %s 成功", filename)
            return 1
            
        except Exception as e:
            logger.error("删除失败: %s", e)
            raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """列出所有知识库，包含display_name"""
        try:
            collection_ids = utility.list_collections()
            mappings = self.get_name_mapping()  # 获取所有映射

            result = []
            for collection_id in collection_ids:
                mapping = mappings.get(collection_id, {})
                result.append({
                    "collection_id": collection_id,
                    "display_name": mapping.get("display_name", collection_id),
                    "created_at": mapping.get("created_at", "")
                })

            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")

    def get_collection_stats(self, collection_id: str) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            if not utility.has_collection(collection_id):
                raise HTTPException(status_code=404, detail=f"知识库 {collection_id} 不存在")

            collection = Collection(collection_id)

            # 确保collection已加载
            try:
                collection.load()
            except Exception as load_err:
                logger.warning("加载collection警告: %s", load_err)

            # 获取实体总数（chunk数）
            total_chunks = collection.num_entities

            # 查询所有文档，获取唯一文件名数量
            try:
                # 查询所有记录的filename字段
                results = collection.query(
                    expr="id > 0",
                    output_fields=["filename", "created_at"]
                )
                results = results[:16384]

                # 统计唯一文件名
                unique_filenames = set()
                latest_update = None

                for result in results:
                    filename = result.get("filename")
                    if filename:
                        unique_filenames.add(filename)

                    # 获取最新更新时间
                    created_at = result.get("created_at")
                    if created_at:
                        if latest_update is None or created_at > latest_update:
                            latest_update = created_at

                total_documents = len(unique_filenames)

            except Exception as query_err:
                logger.warning("查询统计信息失败: %s", query_err)
                total_documents = 0
                latest_update = None

            # 获取显示名称
            mapping = self.get_name_mapping(collection_id)
            display_name = mapping.get("display_name", collection_id)

            return {
                "collection_id": collection_id,
                "collection_name": display_name,  # 前端显示的名称
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "last_updated": latest_update
            }

        except Exception as e:
            logger.error("获取统计信息失败: %s", e)
            raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

    def get_collection_documents(self, collection_id: str) -> List[Dict[str, Any]]:
        """获取知识库中的文档列表（按文件名去重，支持 V1 和 V2）"""
        try:
            if not utility.has_collection(collection_id):
                raise HTTPException(status_code=404, detail=f"知识库 {collection_id} 不存在")

            collection = Collection(collection_id)

            # 确保collection已加载
            try:
                collection.load()
            except Exception as load_err:
                logger.warning("加载collection警告: %s", load_err)

            # 查询所有记录
            try:
                results = collection.query(
                    expr="id > 0",
                    output_fields=["filename", "file_id", "metadata", "created_at"]
                )
                results = results[:16384]

                logger.info("查询知识库文档列表: %s", collection_id)
                logger.info("总记录数: %d", len(results))

                # 按文件名分组统计
                doc_stats = {}
                for idx, result in enumerate(results):
                    filename = result.get("filename")
                    if not filename:
                        continue

                    if filename not in doc_stats:
                        # 解析metadata获取额外信息
                        metadata_str = result.get("metadata", "{}")
                        try:
                            metadata = json.loads(metadata_str)
                        except:
                            metadata = {}

                        # ✅ 关键：从 metadata 中提取文件系统的 file_id
                        # V1: metadata.file_id (如 file_20251016_d398cfa1)
                        # V2: metadata.file_id (UUID 格式，如 bdde5a1e-b522-4de5-9948-2e1d721a7292)
                        # 如果 metadata 中没有，则使用 Milvus 的 file_id
                        actual_file_id = metadata.get("file_id", result.get("file_id"))
                        
                        # 打印前3个文档的 ID 信息
                        if idx < 3:
                            logger.info("文档 %d: %s", idx+1, filename)
                            logger.info("Milvus file_id: %s", result.get("file_id"))
                            logger.info("Metadata file_id: %s", metadata.get("file_id"))
                            logger.info("实际使用 file_id: %s", actual_file_id)
                            logger.info("API version: %s", metadata.get("api_version", "v1"))

                        doc_stats[filename] = {
                            "filename": filename,
                            "file_id": actual_file_id,  # ✅ 使用 metadata 中的 file_id
                            "chunks": 0,
                            "created_at": result.get("created_at"),
                            "metadata": metadata,
                            "api_version": metadata.get("api_version", "v1")  # ✅ 添加版本信息
                        }

                    doc_stats[filename]["chunks"] += 1

                # 转换为列表并排序（按创建时间倒序）
                documents = list(doc_stats.values())
                documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)

                logger.info("去重后文档数: %d", len(documents))

                return documents

            except Exception as query_err:
                logger.error("查询文档列表失败: %s", query_err)
                return []

        except Exception as e:
            logger.error("获取文档列表失败: %s", e)
            raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有知识库的汇总统计信息"""
        try:
            collections = utility.list_collections()

            total_collections = len(collections)
            total_documents = 0
            total_chunks = 0

            collection_details = []

            for collection_name in collections:
                try:
                    stats = self.get_collection_stats(collection_name)
                    total_documents += stats["total_documents"]
                    total_chunks += stats["total_chunks"]
                    collection_details.append(stats)
                except Exception as e:
                    logger.warning("获取 %s 统计信息失败: %s", collection_name, e)
                    continue

            return {
                "total_collections": total_collections,
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "collections": collection_details
            }

        except Exception as e:
            logger.error("获取汇总统计失败: %s", e)
            raise HTTPException(status_code=500, detail=f"获取汇总统计失败: {str(e)}")

# FastAPI 应用
app = FastAPI(title="Milvus RAG Service", version="2.0.0")

# 配置CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)

# 初始化Milvus服务
milvus_service = MilvusRAGService()

@app.post("/knowledge_base/create")
async def create_knowledge_base(display_name: str):
    """创建知识库"""
    try:
        collection_id, success = milvus_service.create_knowledge_base(display_name)

        if success:
            return {
                "status": "success",
                "message": f"知识库 '{display_name}' 创建成功",
                "collection_id": collection_id,
                "display_name": display_name
            }
        else:
            return {
                "status": "error",
                "message": f"知识库创建失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeleteKBByIdRequest(BaseModel):
    collection_id: str

@app.delete("/knowledge_base/delete")
async def delete_knowledge_base(request: DeleteKBByIdRequest):
    """删除知识库"""
    try:
        success = milvus_service.delete_knowledge_base(request.collection_id)
        if success:
            return {"status": "success", "message": f"知识库删除成功"}
        else:
            return {"status": "not_found", "message": f"知识库不存在"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge_base/list")
async def list_knowledge_bases():
    """列出所有知识库"""
    try:
        kbs = milvus_service.list_knowledge_bases()
        return {"status": "success", "knowledge_bases": kbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_json", response_model=UploadResponse)
async def upload_json_file(request: UploadKBRequest):
    """上传JSON文件到知识库（V1 格式）"""
    try:
        # 解析JSON文件
        documents = milvus_service.parse_json_file(request.file_data)
        
        if not documents:
            raise HTTPException(status_code=400, detail="未找到有效的文档chunks")
        
        # 插入文档
        file_ids = milvus_service.insert_documents(request.collection_name, documents)
        
        # 获取文件名
        filename = request.file_data.get("filename", "unknown.txt")
        if filename.startswith("/"):
            filename = os.path.basename(filename)
        
        response = UploadResponse(
            filename=filename,
            file_id=documents[0].file_id if documents else str(uuid.uuid4()),
            status="success",
            message=f"文件上传成功（V1），处理了{len(documents)}个chunks",
            chunks_count=len(documents)
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_json/v2")
async def upload_json_file_v2(request: Dict[str, Any]):
    """
    上传 output.json 格式的数据到知识库（OCR 2.0）
    
    请求格式：
    {
      "collection_name": "kb_123",
      "file_id": "原始file_id",  // 必须，用于前端查找文件
      "output_json": {
        "backend": "pipeline",
        "version": "2.5.4",
        "results": {
          "文件名": {
            "md_content": "...",
            "chunks": [...],
            "images": {...},
            "page_images": [...]
          }
        }
      },
      "result_key": "文件名"  // 可选
    }
    
    返回：存储结果
    """
    try:
        
        # 提取请求参数
        collection_name = request.get("collection_name")
        file_id_original = request.get("file_id")  # 原始 file_id
        output_json = request.get("output_json", {})
        result_key = request.get("result_key")
        
        if not collection_name:
            raise HTTPException(status_code=400, detail="缺少 collection_name 参数")
        
        if not file_id_original:
            raise HTTPException(status_code=400, detail="缺少 file_id 参数")
        
        logger.info("请求参数:")
        logger.info("Collection: %s", collection_name)
        logger.info("File ID: %s", file_id_original)
        logger.info("Result Key: %s", result_key or "(自动)")
        
        # 提取 results
        results = output_json.get("results", {})
        if not results:
            logger.error("output_json 结构:")
            logger.info("Keys: %s", list(output_json.keys()))
            raise HTTPException(status_code=400, detail="output_json 中未找到 results 字段")
        
        # 获取 result_key
        if not result_key or result_key not in results:
            result_key = list(results.keys())[0]
            logger.info("使用第一个键作为 result_key: %s", result_key)
        
        result_data = results[result_key]
        
        logger.info("输入数据信息:")
        logger.info("Backend: %s", output_json.get("backend", "N/A"))
        logger.info("Version: %s", output_json.get("version", "N/A"))
        logger.info("Result Key: %s", result_key)
        logger.info("包含字段: %s", list(result_data.keys()))
        logger.info("是否有 md_content: %s", "md_content" in result_data)
        logger.info("是否有 chunks: %s", "chunks" in result_data)
        logger.info("是否有 images: %s", "images" in result_data)
        logger.info("是否有 page_images: %s", "page_images" in result_data)
        
        if 'md_content' in result_data:
            logger.info("md_content 长度: %d 字符", len(result_data["md_content"]))
        
        # 提取 chunks
        chunks = result_data.get("chunks", [])
        if not chunks:
            logger.error("未找到 chunks 或 chunks 为空")
            raise HTTPException(status_code=400, detail="未找到 chunks 字段或 chunks 为空")
        
        logger.info("总 chunks: %d", len(chunks))
        
        # 打印前3个 chunks 的结构
        logger.info("前 3 个 chunks 结构:")
        for i, chunk in enumerate(chunks[:3]):
            logger.info("Chunk %d:", i+1)
            logger.info("Keys: %s", list(chunk.keys()))
            logger.info("页码: %s-%s", chunk.get("page_start"), chunk.get("page_end"))
            logger.info("文本长度: %s", chunk.get("text_length"))
            logger.info("文本预览: %s...", chunk.get("text", "")[:50])
        
        # 构建 DocumentChunk 列表
        logger.info("开始构建 DocumentChunk 列表...")
        documents = []
        filename = result_key + ".pdf"  # 恢复文件名
        
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.get("text", "")
            if not chunk_text.strip():
                logger.warning("跳过空 chunk %d", i)
                continue
            
            # 构建 metadata（包含 V2 的额外字段 + 原始 file_id）
            metadata = {
                "file_id": file_id_original,  # 保存原始 file_id
                "page_start": chunk.get("page_start", 1),
                "page_end": chunk.get("page_end", 1),
                "pages": chunk.get("pages", [1]),
                "text_length": chunk.get("text_length", len(chunk_text)),
                "continued": chunk.get("continued", False),
                "cross_page_bridge": chunk.get("cross_page_bridge", False),
                "is_table_like": chunk.get("is_table_like", False),
                "chunk_index": i,
                "headers": chunk.get("headers", {}),  # V2 特有
                "extraction_method": output_json.get("backend", "unknown"),  # V2 特有
                "version": output_json.get("version", "unknown"),  # V2 特有
                "api_version": "v2"  # 标记为 V2 数据
            }
            
            doc = DocumentChunk(
                chunk_text=chunk_text,
                filename=filename,
                file_id=file_id_original,  # ✅ 使用原始 file_id
                metadata=metadata
            )
            documents.append(doc)
        
        logger.info("构建完成，有效 chunks: %d", len(documents))
        
        # 插入到 Milvus
        logger.info("开始插入到 Milvus（Collection: %s）...", collection_name)
        file_ids = milvus_service.insert_documents(collection_name, documents)
        
        logger.info("=" * 80)
        logger.info("OCR 2.0 数据存储完成")
        logger.info("=" * 80)
        logger.info("存储统计:")
        logger.info("Collection: %s", collection_name)
        logger.info("文件名: %s", filename)
        logger.info("插入数量: %d", len(file_ids))
        logger.info("Backend: %s", output_json.get("backend"))
        logger.info("Version: %s", output_json.get("version"))
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "message": f"OCR 2.0 数据上传成功，处理了 {len(documents)} 个 chunks",
            "collection_name": collection_name,
            "filename": filename,
            "chunks_count": len(documents),
            "backend": output_json.get("backend"),
            "version": output_json.get("version")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("=" * 80)
        logger.error("OCR 2.0 数据存储失败")
        logger.error("=" * 80)
        logger.error("错误: %s", e)
        import traceback
        logger.error("存储失败", exc_info=True)
        logger.info("=" * 80)
        raise HTTPException(status_code=500, detail=f"OCR 2.0 数据存储失败: {str(e)}")

@app.post("/search")
async def search_documents(request: SearchRequest):
    """根据问题搜索相似文档"""
    try:
        results = milvus_service.search_by_text(
            collection_name=request.collection_name,
            query_text=request.query_text,
            top_k=request.top_k,
            filter_expr=request.filter_expr
        )
        
        return {
            "status": "success",
            "query": request.query_text,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_by_filename")
async def search_by_filename(request: SearchByFilenameRequest):
    """根据文件名检索知识库内信息"""
    try:
        results = milvus_service.search_by_filename(
            collection_name=request.collection_name,
            filename=request.filename,
            top_k=request.top_k
        )
        
        return {
            "status": "success",
            "filename": request.filename,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete")
async def delete_documents(request: DeleteRequest):
    """删除文档"""
    try:
        deleted_count = milvus_service.delete_documents_by_filename(
            collection_name=request.collection_name,
            filename=request.filename
        )
        
        return {
            "status": "success",
            "message": f"已删除文件 {request.filename}",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "Milvus RAG Service"}

@app.get("/stats/collection/{collection_name}")
async def get_collection_stats(collection_name: str):
    """获取单个知识库的统计信息"""
    try:
        stats = milvus_service.get_collection_stats(collection_name)
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/all")
async def get_all_stats():
    """获取所有知识库的汇总统计信息"""
    try:
        stats = milvus_service.get_all_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge_base/{collection_id}/documents")
async def get_knowledge_base_documents(collection_id: str):
    """获取知识库中的文档列表"""
    try:
        documents = milvus_service.get_collection_documents(collection_id)
        stats = milvus_service.get_collection_stats(collection_id)

        return {
            "status": "success",
            "collection_id": collection_id,
            "collection_name": stats["collection_name"],
            "total_documents": stats["total_documents"],
            "total_chunks": stats["total_chunks"],
            "last_updated": stats["last_updated"],
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document/{file_id}/details")
async def get_document_details(file_id: str):
    """获取文档的详细信息，包括PDF、Markdown、chunks等（支持 V1 和 V2）"""
    try:
        logger.info("=" * 80)
        logger.info("获取文档详情请求 - /document/%s/details", file_id)
        logger.info("=" * 80)
        logger.info("File ID: %s", file_id)
        
        # 定义基础路径（V1 和 V2 现在都使用同一个路径，从环境变量读取）
        import os
        upload_base = Path(os.getenv(
            "UPLOAD_BASE_DIR",
            "./backend/output/uploads"
        ))
        extraction_base = Path(os.getenv(
            "EXTRACTION_RESULTS_DIR",
            "./backend/output/extraction_results"
        ))
        
        base_dirs_v1 = {
            'upload': upload_base,
            'extraction': extraction_base
        }
        base_dirs_v2 = {
            'upload': upload_base,
            'extraction': extraction_base
        }
        
        # 查找文件目录
        logger.info("查找文件...")
        
        extraction_dir = extraction_base / file_id
        base_upload_dir = upload_base
        
        if not extraction_dir.exists():
            logger.warning("目录不存在: %s", extraction_dir)
            raise HTTPException(status_code=404, detail=f"文档 {file_id} 不存在")
        
        logger.info("找到目录: %s", extraction_dir)
        
        # 通过文件特征判断版本（V1 vs V2）
        # V2特征：有 *_extraction.md 或 *_chunked_output.json 文件
        # V1特征：有 chunks.json 和 *.md (不含_extraction后缀)
        has_v2_extraction = len(list(extraction_dir.glob("*_extraction.md"))) > 0
        has_v2_chunked = len(list(extraction_dir.glob("*_chunked_output.json"))) > 0
        has_v1_chunks = (extraction_dir / "chunks.json").exists()
        
        if has_v2_extraction or has_v2_chunked:
            api_version = "v2"
            logger.info("识别为 V2 格式 (有 *_extraction.md 或 *_chunked_output.json)")
        elif has_v1_chunks:
            api_version = "v1"
            logger.info("识别为 V1 格式 (有 chunks.json)")
        else:
            # 默认为V1（兼容老数据）
            api_version = "v1"
            logger.warning("无法明确识别版本，默认使用 V1")
        
        logger.info("使用版本: %s", api_version)
        
        # 读取metadata.json（V1 和 V2 通用）或者 V2 的 metadata 文件
        metadata_files = list(extraction_dir.glob("*_metadata.json")) + [extraction_dir / "metadata.json"]
        metadata_path = None
        for mf in metadata_files:
            if mf.exists():
                metadata_path = mf
                break
        
        if not metadata_path:
            logger.warning("未找到 metadata 文件")
            raise HTTPException(status_code=404, detail="元数据文件不存在")

        logger.info("找到 metadata: %s", metadata_path.name)
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 读取chunks（V1 和 V2 格式不同）
        logger.info("读取 chunks...")
        chunks_data = []
        
        if api_version == "v2":
            # V2: 从 chunked_output.json 中读取
            chunked_files = list(extraction_dir.glob("*_chunked_output.json"))
            if chunked_files:
                chunked_file = chunked_files[0]
                logger.info("V2 格式: %s", chunked_file.name)
                with open(chunked_file, 'r') as f:
                    chunked_json = json.load(f)
                    # 从 results 中提取 chunks
                    results = chunked_json.get('results', {})
                    if results:
                        result_key = list(results.keys())[0]
                        chunks_data = results[result_key].get('chunks', [])
                logger.info("读取到 %d 个 chunks (V2)", len(chunks_data))
            else:
                logger.warning("未找到 V2 chunked_output.json")
        else:
            # V1: 从 chunks.json 中读取
            chunks_path = extraction_dir / "chunks.json"
            if chunks_path.exists():
                logger.info("V1 格式: chunks.json")
                with open(chunks_path, 'r') as f:
                    full_chunks = json.load(f)
                    if isinstance(full_chunks, dict) and 'chunks' in full_chunks:
                        chunks_data = full_chunks.get('chunks', [])
                    else:
                        chunks_data = full_chunks
                logger.info("读取到 %d 个 chunks (V1)", len(chunks_data))

        # 读取markdown（V1 和 V2 格式不同）
        logger.info("读取 markdown...")
        markdown_content = ""
        
        if api_version == "v2":
            # V2: 从 *_extraction.md 读取
            md_files = list(extraction_dir.glob("*_extraction.md"))
            if md_files:
                md_file = md_files[0]
                logger.info("V2 格式: %s", md_file.name)
                with open(md_file, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                logger.info("Markdown 长度: %d 字符 (V2)", len(markdown_content))
        else:
            # V1: 从文件名.md 读取
            markdown_path = extraction_dir / f"{metadata['filename'].replace('.pdf', '.md')}"
            if markdown_path.exists():
                logger.info("V1 格式: %s", markdown_path.name)
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                logger.info("Markdown 长度: %d 字符 (V1)", len(markdown_content))

        # 查找PDF文件（V1 和 V2 路径不同）
        logger.info("查找 PDF 文件...")
        pdf_filename_pattern = f"*{file_id}*{metadata['filename']}"
        pdf_path = None
        
        # 递归查找
        for pdf_file in base_upload_dir.rglob("*.pdf"):
            if file_id in pdf_file.name and metadata['filename'] in pdf_file.name:
                pdf_path = pdf_file
                logger.info("找到 PDF: %s", pdf_path)
                break
        
        if not pdf_path:
            logger.warning("未找到 PDF 文件")

        logger.info("=" * 80)
        logger.info("文档详情提取完成 (%s)", api_version.upper())
        logger.info("=" * 80)
        logger.info("Filename: %s", metadata.get('filename'))
        logger.info("Chunks: %d", len(chunks_data))
        logger.info("Markdown: %d 字符", len(markdown_content))
        logger.info("PDF: %s", "有" if pdf_path else "无")
        logger.info("=" * 80)

        return {
            "status": "success",
            "file_id": file_id,
            "filename": metadata.get('filename'),
            "api_version": api_version,  # ✅ 返回版本信息
            "metadata": metadata.get('metadata', {}) if api_version == "v1" else metadata,
            "extraction_time": metadata.get('extraction_time'),
            "extraction_mode": metadata.get('extraction_mode'),  # V2 特有
            "markdown": markdown_content,
            "chunks": chunks_data,
            "pdf_url": f"/document/{file_id}/pdf" if pdf_path else None,
            "total_chunks": len(chunks_data),
            "total_pages": metadata.get('total_pages', 0) if api_version == "v2" else metadata.get('metadata', {}).get('total_pages', 0),
            "total_images": metadata.get('total_images', 0) if api_version == "v2" else metadata.get('metadata', {}).get('total_images', 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取文档详情失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")

@app.get("/document/{file_id}/pdf")
async def get_document_pdf(file_id: str):
    """直接返回PDF文件，Content-Disposition设置为inline以便浏览器内嵌显示（支持 V1 和 V2）"""
    try:
        logger.info("获取 PDF 文件请求: %s", file_id)
        
        # 定义基础路径（V1 和 V2 现在都使用同一个路径，从环境变量读取）
        import os
        upload_base = Path(os.getenv(
            "UPLOAD_BASE_DIR",
            "./backend/output/uploads"
        ))
        extraction_base = Path(os.getenv(
            "EXTRACTION_RESULTS_DIR",
            "./backend/output/extraction_results"
        ))
        
        base_dirs_v1 = {
            'upload': upload_base,
            'extraction': extraction_base
        }
        base_dirs_v2 = {
            'upload': upload_base,
            'extraction': extraction_base
        }
        
        # 查找文件目录
        extraction_dir = extraction_base / file_id
        base_upload_dir = upload_base
        
        if not extraction_dir.exists():
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 通过文件特征判断版本（V1 vs V2）
        has_v2_extraction = len(list(extraction_dir.glob("*_extraction.md"))) > 0
        has_v2_chunked = len(list(extraction_dir.glob("*_chunked_output.json"))) > 0
        has_v1_chunks = (extraction_dir / "chunks.json").exists()
        
        if has_v2_extraction or has_v2_chunked:
            api_version = "v2"
        elif has_v1_chunks:
            api_version = "v1"
        else:
            api_version = "v1"  # 默认V1
        
        logger.info("使用版本: %s", api_version)
        
        # 读取metadata
        metadata_files = list(extraction_dir.glob("*_metadata.json")) + [extraction_dir / "metadata.json"]
        metadata_path = None
        for mf in metadata_files:
            if mf.exists():
                metadata_path = mf
                break
        
        if not metadata_path:
            raise HTTPException(status_code=404, detail="metadata文件不存在")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 查找PDF文件
        filename = metadata.get('filename', '')
        pdf_path = None
        
        # 递归查找
        for pdf_file in base_upload_dir.rglob("*.pdf"):
            if file_id in pdf_file.name and filename in pdf_file.name:
                pdf_path = pdf_file
                break

        if not pdf_path or not pdf_path.exists():
            logger.warning("PDF 文件未找到")
            raise HTTPException(status_code=404, detail="PDF文件不存在")

        logger.info("找到 PDF: %s", pdf_path)

        # 返回PDF，设置为inline模式以便浏览器内嵌显示
        from fastapi.responses import Response
        from urllib.parse import quote
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()

        # URL encode the filename for proper handling of Chinese characters
        encoded_filename = quote(filename)

        logger.info("返回 PDF (%s): %s", api_version.upper(), filename)

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取PDF文件失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取PDF文件失败: {str(e)}")

@app.get("/document/{file_id}/images/{image_name}")
async def get_document_image(file_id: str, image_name: str):
    """获取文档提取的图片"""
    try:
        base_extraction_dir = Path(os.getenv(
            "EXTRACTION_RESULTS_DIR",
            "./backend/output/extraction_results"
        ))

        # 图片路径
        image_path = base_extraction_dir / file_id / "images" / image_name

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="图片不存在")

        # 根据文件扩展名设置media_type
        ext = image_path.suffix.lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_types.get(ext, 'image/png')

        return FileResponse(
            path=str(image_path),
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取图片失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")

if __name__ == "__main__":
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    logger.info("=" * 60)
    logger.info("Starting Milvus RAG Service")
    logger.info("=" * 60)
    logger.info("Server: http://%s:%d", host, port)
    logger.info("Docs: http://%s:%d/docs", host, port)
    logger.info("=" * 60)
    
    uvicorn.run(app, host=host, port=port)