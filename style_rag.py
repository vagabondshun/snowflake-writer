"""
Style RAG - 风格模仿的向量检索系统
使用向量数据库存储和检索参考小说的风格样本
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import json

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class StyleRAGError(Exception):
    """RAG系统相关错误"""
    pass


class DependencyError(StyleRAGError):
    """依赖包未安装错误"""
    pass


class StyleRAG:
    """
    风格RAG系统 - 向量检索增强的风格模仿

    功能：
    1. 导入参考小说并自动分块
    2. 使用向量数据库存储段落
    3. 根据当前场景内容检索相似风格段落
    4. 提供风格上下文用于生成

    依赖：
    - chromadb: 向量数据库
    - sentence-transformers: 文本向量化
    """

    def __init__(self, project_path: Path):
        """
        初始化RAG系统

        Args:
            project_path: 项目路径
        """
        # 检查依赖
        if not CHROMADB_AVAILABLE:
            raise DependencyError(
                "ChromaDB未安装。请运行: pip install chromadb"
            )

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise DependencyError(
                "sentence-transformers未安装。请运行: pip install sentence-transformers"
            )

        self.project_path = project_path
        self.style_ref_path = project_path / "style_references"
        self.style_ref_path.mkdir(exist_ok=True)

        # ChromaDB配置
        chroma_path = project_path / ".chroma"
        self.client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建collection
        self.collection = self.client.get_or_create_collection(
            name="style_references",
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )

        # 加载embedding模型（使用轻量级中文模型）
        # 可以更换为其他模型，如 'paraphrase-multilingual-MiniLM-L12-v2'
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

        # 加载元数据
        self.metadata_path = self.style_ref_path / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """加载风格参考元数据"""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"references": {}}

    def _save_metadata(self):
        """保存风格参考元数据"""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """
        智能文本分块

        Args:
            text: 原始文本
            chunk_size: 每块目标字符数

        Returns:
            分块列表，每个块包含text和metadata
        """
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text.strip())

        chunks = []
        current_chunk = ""
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            # 如果当前块+新段落超过目标大小，保存当前块
            if current_length > 0 and current_length + para_length > chunk_size * 1.5:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "char_count": current_length
                    })
                current_chunk = para
                current_length = para_length
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                current_length += para_length

        # 保存最后一块
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "char_count": current_length
            })

        return chunks

    def _classify_chunk_type(self, text: str) -> str:
        """
        简单的块类型分类

        Returns:
            'dialogue' | 'action' | 'description' | 'mixed'
        """
        # 统计对话标记
        dialogue_markers = text.count('"') + text.count('"') + text.count('"')
        dialogue_ratio = dialogue_markers / max(len(text), 1)

        # 统计动作动词（简化版）
        action_verbs = ['跑', '走', '打', '踢', '跳', '冲', '扑', '抓', '推']
        action_count = sum(text.count(verb) for verb in action_verbs)

        if dialogue_ratio > 0.1:
            return 'dialogue'
        elif action_count > 3:
            return 'action'
        elif len(text) > 300:
            return 'description'
        else:
            return 'mixed'

    def add_reference_novel(
        self,
        title: str,
        content: str,
        author: str = None,
        chunk_size: int = 500,
        max_chunks: int = 100
    ) -> Dict[str, Any]:
        """
        添加参考小说到向量数据库

        Args:
            title: 小说标题
            content: 小说全文
            author: 作者（可选）
            chunk_size: 分块大小
            max_chunks: 最大块数（避免过大）

        Returns:
            添加结果统计
        """
        # 生成参考ID
        ref_id = hashlib.md5(title.encode()).hexdigest()[:8]

        # 检查是否已存在
        if ref_id in self.metadata["references"]:
            raise StyleRAGError(f"参考小说 '{title}' 已存在，请先删除")

        # 分块
        chunks = self._chunk_text(content, chunk_size)

        # 限制块数量
        if len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]

        # 准备数据
        texts = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{ref_id}_chunk_{i}"
            chunk_type = self._classify_chunk_type(chunk["text"])

            texts.append(chunk["text"])
            metadatas.append({
                "ref_id": ref_id,
                "title": title,
                "author": author or "Unknown",
                "chunk_index": i,
                "chunk_type": chunk_type,
                "char_count": chunk["char_count"]
            })
            ids.append(chunk_id)

        # 生成embeddings并添加到数据库
        embeddings = self.model.encode(texts, show_progress_bar=True)

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

        # 更新元数据
        self.metadata["references"][ref_id] = {
            "title": title,
            "author": author,
            "chunk_count": len(chunks),
            "total_chars": sum(c["char_count"] for c in chunks),
            "added_at": None  # 可以添加时间戳
        }
        self._save_metadata()

        return {
            "ref_id": ref_id,
            "title": title,
            "chunks_added": len(chunks),
            "total_chars": sum(c["char_count"] for c in chunks)
        }

    def retrieve_style_samples(
        self,
        query: str,
        n_results: int = 3,
        chunk_type: Optional[str] = None,
        ref_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相似的风格样本

        Args:
            query: 查询文本（当前场景内容）
            n_results: 返回结果数量
            chunk_type: 限制块类型 ('dialogue', 'action', 'description')
            ref_id: 限制特定参考小说

        Returns:
            样本列表，包含text、metadata、distance
        """
        # 构建过滤条件
        where = {}
        if chunk_type:
            where["chunk_type"] = chunk_type
        if ref_id:
            where["ref_id"] = ref_id

        # 检索
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where if where else None
        )

        # 格式化结果
        samples = []
        if results["documents"] and len(results["documents"]) > 0:
            for i in range(len(results["documents"][0])):
                samples.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })

        return samples

    def get_style_context(
        self,
        scene_description: str,
        scene_type: Optional[str] = None,
        n_samples: int = 3
    ) -> Dict[str, Any]:
        """
        获取完整的风格上下文（用于生成）

        Args:
            scene_description: 场景描述
            scene_type: 场景类型提示
            n_samples: 样本数量

        Returns:
            风格上下文字典
        """
        # 映射场景类型到块类型
        type_mapping = {
            "dialogue": "dialogue",
            "action": "action",
            "narrative": "description",
            "description": "description"
        }
        chunk_type = type_mapping.get(scene_type)

        # 检索样本
        samples = self.retrieve_style_samples(
            query=scene_description,
            n_results=n_samples,
            chunk_type=chunk_type
        )

        return {
            "samples": samples,
            "sample_count": len(samples),
            "references": list(self.metadata["references"].values())
        }

    def list_references(self) -> List[Dict[str, Any]]:
        """列出所有参考小说"""
        return [
            {"ref_id": ref_id, **info}
            for ref_id, info in self.metadata["references"].items()
        ]

    def remove_reference(self, ref_id: str) -> bool:
        """
        删除参考小说

        Args:
            ref_id: 参考ID

        Returns:
            是否成功删除
        """
        if ref_id not in self.metadata["references"]:
            return False

        # 从向量数据库中删除所有相关chunks
        # ChromaDB支持通过metadata过滤删除
        try:
            # 获取所有该参考的IDs
            results = self.collection.get(where={"ref_id": ref_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])

            # 从元数据中删除
            del self.metadata["references"][ref_id]
            self._save_metadata()

            return True
        except Exception as e:
            raise StyleRAGError(f"删除参考失败: {str(e)}")

    def clear_all_references(self):
        """清除所有参考小说"""
        # 删除collection并重建
        self.client.delete_collection("style_references")
        self.collection = self.client.get_or_create_collection(
            name="style_references",
            metadata={"hnsw:space": "cosine"}
        )

        # 清空元数据
        self.metadata = {"references": {}}
        self._save_metadata()

    def get_statistics(self) -> Dict[str, Any]:
        """获取RAG系统统计信息"""
        total_chunks = sum(
            ref["chunk_count"]
            for ref in self.metadata["references"].values()
        )
        total_chars = sum(
            ref["total_chars"]
            for ref in self.metadata["references"].values()
        )

        return {
            "reference_count": len(self.metadata["references"]),
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "collection_count": self.collection.count()
        }


def check_dependencies() -> Dict[str, bool]:
    """
    检查RAG依赖是否已安装

    Returns:
        依赖状态字典
    """
    return {
        "chromadb": CHROMADB_AVAILABLE,
        "sentence_transformers": SENTENCE_TRANSFORMERS_AVAILABLE,
        "all_available": CHROMADB_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE
    }


def install_instructions() -> str:
    """返回依赖安装说明"""
    return """
RAG风格系统依赖安装：

pip install chromadb sentence-transformers

或者一次性安装：

pip install chromadb sentence-transformers torch

注意：sentence-transformers需要PyTorch，如果未安装会自动安装。
首次运行会下载embedding模型（约90MB），请确保网络连接正常。
"""
