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

# 文件格式解析依赖
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


# ==================== 全局配置 ====================
# 默认全局资料库路径（可通过环境变量覆盖）
DEFAULT_GLOBAL_LIBRARY_PATH = Path.home() / "style_references"

def get_global_library_path() -> Path:
    """获取全局资料库路径"""
    env_path = os.environ.get("SNOWFLAKE_STYLE_LIBRARY")
    if env_path:
        return Path(env_path)
    return DEFAULT_GLOBAL_LIBRARY_PATH


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

        # 加载embedding模型（中文优化模型）
        # 其他可选模型:
        # - 'paraphrase-multilingual-MiniLM-L12-v2' (多语言，470MB)
        # - 'paraphrase-MiniLM-L6-v2' (英文，90MB)
        self.model = SentenceTransformer('shibing624/text2vec-base-chinese')

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
        智能文本分块（优化版）

        Args:
            text: 原始文本
            chunk_size: 每块目标字符数

        Returns:
            分块列表，每个块包含text和metadata
        """
        # 预处理：统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 按多种分隔符分割成段落（优先双换行，其次单换行）
        # 先尝试双换行分割
        paragraphs = re.split(r'\n\s*\n', text.strip())

        # 如果分割后段落太少或太大，尝试单换行分割
        if len(paragraphs) < 5 or any(len(p) > chunk_size * 3 for p in paragraphs):
            paragraphs = text.strip().split('\n')

        chunks = []
        current_chunk = ""
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果单个段落超过目标大小的2倍，按句子强制分割
            if len(para) > chunk_size * 2:
                sub_chunks = self._split_long_paragraph(para, chunk_size)
                for sub in sub_chunks:
                    # 先保存当前块
                    if current_chunk and current_length >= chunk_size * 0.5:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "char_count": current_length
                        })
                        current_chunk = ""
                        current_length = 0

                    # 添加子块
                    if current_chunk:
                        current_chunk += "\n" + sub
                        current_length += len(sub)
                    else:
                        current_chunk = sub
                        current_length = len(sub)

                    # 如果达到目标大小，保存
                    if current_length >= chunk_size:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "char_count": current_length
                        })
                        current_chunk = ""
                        current_length = 0
                continue

            para_length = len(para)

            # 如果当前块+新段落超过目标大小，保存当前块
            if current_length > 0 and current_length + para_length > chunk_size * 1.2:
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
                    current_chunk += "\n" + para
                else:
                    current_chunk = para
                current_length += para_length

        # 保存最后一块
        if current_chunk and current_length > 50:  # 忽略太短的块
            chunks.append({
                "text": current_chunk.strip(),
                "char_count": current_length
            })

        return chunks

    def _split_long_paragraph(self, text: str, chunk_size: int) -> List[str]:
        """
        按句子分割超长段落

        Args:
            text: 长段落文本
            chunk_size: 目标块大小

        Returns:
            分割后的文本列表
        """
        # 中文句子分隔符
        sentence_endings = r'([。！？!?…]+["」』]?|[.!?]+["\']?\s)'
        sentences = re.split(sentence_endings, text)

        # 重组句子（分割会丢失分隔符，需要重新拼接）
        result_sentences = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and re.match(sentence_endings, sentences[i + 1] or ''):
                result_sentences.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                if sentences[i].strip():
                    result_sentences.append(sentences[i])
                i += 1

        # 按目标大小组合句子
        chunks = []
        current = ""

        for sent in result_sentences:
            sent = sent.strip()
            if not sent:
                continue

            if len(current) + len(sent) > chunk_size and current:
                chunks.append(current)
                current = sent
            else:
                current = current + sent if current else sent

        if current:
            chunks.append(current)

        return chunks if chunks else [text]

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
        max_chunks: int = 200
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

        # 使用自定义模型生成查询向量（避免维度不匹配）
        query_embedding = self.model.encode([query]).tolist()

        # 检索
        results = self.collection.query(
            query_embeddings=query_embedding,
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

    # ==================== 文件解析功能 ====================

    def _parse_txt(self, file_path: Path) -> str:
        """解析TXT文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise StyleRAGError(f"无法解析TXT文件，尝试的编码: {encodings}")

    def _parse_pdf(self, file_path: Path) -> str:
        """解析PDF文件"""
        if not PYPDF2_AVAILABLE:
            raise DependencyError("PDF解析需要PyPDF2。请运行: pip install PyPDF2")

        text_parts = []
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            raise StyleRAGError(f"PDF解析失败: {str(e)}")

        if not text_parts:
            raise StyleRAGError("PDF文件无法提取文本（可能是扫描件或图片PDF）")

        return "\n\n".join(text_parts)

    def _parse_epub(self, file_path: Path) -> str:
        """解析EPUB文件"""
        if not EBOOKLIB_AVAILABLE:
            raise DependencyError("EPUB解析需要ebooklib。请运行: pip install ebooklib")
        if not BS4_AVAILABLE:
            raise DependencyError("EPUB解析需要BeautifulSoup。请运行: pip install beautifulsoup4")

        text_parts = []
        try:
            book = epub.read_epub(str(file_path))

            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')

                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # 提取文本
                    text = soup.get_text(separator='\n')

                    # 清理空行
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    if lines:
                        text_parts.append('\n'.join(lines))

        except Exception as e:
            raise StyleRAGError(f"EPUB解析失败: {str(e)}")

        if not text_parts:
            raise StyleRAGError("EPUB文件无法提取文本")

        return "\n\n".join(text_parts)

    def parse_file(self, file_path: str | Path) -> Dict[str, Any]:
        """
        解析文件并返回内容

        Args:
            file_path: 文件路径

        Returns:
            包含 content, title, format 的字典

        Raises:
            StyleRAGError: 如果格式不支持或解析失败
        """
        path = Path(file_path)

        if not path.exists():
            raise StyleRAGError(f"文件不存在: {path}")

        suffix = path.suffix.lower()
        title = path.stem  # 使用文件名作为默认标题

        if suffix == '.txt':
            content = self._parse_txt(path)
            file_format = 'txt'
        elif suffix == '.pdf':
            content = self._parse_pdf(path)
            file_format = 'pdf'
        elif suffix == '.epub':
            content = self._parse_epub(path)
            file_format = 'epub'
        else:
            raise StyleRAGError(
                f"不支持的文件格式: {suffix}\n"
                "支持的格式: .txt, .pdf, .epub"
            )

        return {
            "content": content,
            "title": title,
            "format": file_format,
            "file_path": str(path),
            "char_count": len(content)
        }

    def add_reference_from_file(
        self,
        file_path: str | Path,
        title: str = None,
        author: str = None,
        chunk_size: int = 500,
        max_chunks: int = 200
    ) -> Dict[str, Any]:
        """
        从文件添加参考小说

        Args:
            file_path: 文件路径（支持 .txt, .pdf, .epub）
            title: 小说标题（可选，默认使用文件名）
            author: 作者（可选）
            chunk_size: 分块大小
            max_chunks: 最大块数

        Returns:
            添加结果统计

        Example:
            result = rag.add_reference_from_file("百年孤独.epub", author="马尔克斯")
        """
        # 解析文件
        parsed = self.parse_file(file_path)

        # 使用提供的标题或文件名
        final_title = title or parsed["title"]

        # 添加到向量库
        result = self.add_reference_novel(
            title=final_title,
            content=parsed["content"],
            author=author,
            chunk_size=chunk_size,
            max_chunks=max_chunks
        )

        # 添加文件信息
        result["source_file"] = parsed["file_path"]
        result["source_format"] = parsed["format"]

        return result

    def scan_folder(
        self,
        folder_path: str | Path,
        author: str = None,
        chunk_size: int = 500,
        max_chunks: int = 200,
        skip_errors: bool = True
    ) -> Dict[str, Any]:
        """
        扫描文件夹并导入所有支持的文件

        Args:
            folder_path: 文件夹路径
            author: 默认作者（可选）
            chunk_size: 分块大小
            max_chunks: 每个文件的最大块数
            skip_errors: 是否跳过错误继续处理

        Returns:
            导入结果统计

        Example:
            result = rag.scan_folder("./参考小说/", author="合集")
        """
        folder = Path(folder_path)

        if not folder.exists():
            raise StyleRAGError(f"文件夹不存在: {folder}")

        if not folder.is_dir():
            raise StyleRAGError(f"路径不是文件夹: {folder}")

        # 支持的扩展名
        supported_extensions = {'.txt', '.pdf', '.epub'}

        # 查找所有文件
        files = []
        for ext in supported_extensions:
            files.extend(folder.glob(f"*{ext}"))
            files.extend(folder.glob(f"*{ext.upper()}"))

        results = {
            "total_files": len(files),
            "success": [],
            "failed": [],
            "skipped": []
        }

        for file_path in files:
            try:
                # 检查是否已存在
                title = file_path.stem
                ref_id = hashlib.md5(title.encode()).hexdigest()[:8]

                if ref_id in self.metadata["references"]:
                    results["skipped"].append({
                        "file": str(file_path),
                        "reason": "已存在"
                    })
                    continue

                # 导入文件
                result = self.add_reference_from_file(
                    file_path=file_path,
                    author=author,
                    chunk_size=chunk_size,
                    max_chunks=max_chunks
                )
                results["success"].append(result)

            except Exception as e:
                error_info = {
                    "file": str(file_path),
                    "error": str(e)
                }
                results["failed"].append(error_info)

                if not skip_errors:
                    raise StyleRAGError(f"导入失败: {file_path}\n{str(e)}")

        results["success_count"] = len(results["success"])
        results["failed_count"] = len(results["failed"])
        results["skipped_count"] = len(results["skipped"])

        return results

    # ==================== 全局资料库功能 ====================

    def list_global_authors(self, library_path: str | Path = None) -> List[Dict[str, Any]]:
        """
        列出全局资料库中的所有作家（子文件夹）

        Args:
            library_path: 资料库路径，默认使用全局配置

        Returns:
            作家列表，每项包含 name, path, file_count
        """
        lib_path = Path(library_path) if library_path else get_global_library_path()

        if not lib_path.exists():
            return []

        authors = []
        supported_extensions = {'.txt', '.pdf', '.epub'}

        for item in lib_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 统计该作家目录下的文件数
                file_count = 0
                for ext in supported_extensions:
                    file_count += len(list(item.glob(f"*{ext}")))
                    file_count += len(list(item.glob(f"*{ext.upper()}")))

                if file_count > 0:
                    authors.append({
                        "name": item.name,
                        "path": str(item),
                        "file_count": file_count
                    })

        return sorted(authors, key=lambda x: x["name"])

    def scan_author(
        self,
        author_name: str,
        library_path: str | Path = None,
        chunk_size: int = 500,
        max_chunks: int = 200,
        skip_errors: bool = True
    ) -> Dict[str, Any]:
        """
        扫描并导入指定作家的所有作品

        Args:
            author_name: 作家名（对应子文件夹名）
            library_path: 资料库路径，默认使用全局配置
            chunk_size: 分块大小
            max_chunks: 每个文件的最大块数
            skip_errors: 是否跳过错误

        Returns:
            导入结果统计

        Example:
            result = rag.scan_author("马尔克斯")
        """
        lib_path = Path(library_path) if library_path else get_global_library_path()
        author_path = lib_path / author_name

        if not author_path.exists():
            raise StyleRAGError(f"作家目录不存在: {author_path}")

        if not author_path.is_dir():
            raise StyleRAGError(f"路径不是目录: {author_path}")

        # 使用 scan_folder，但设置作者为文件夹名
        return self.scan_folder(
            folder_path=author_path,
            author=author_name,
            chunk_size=chunk_size,
            max_chunks=max_chunks,
            skip_errors=skip_errors
        )

    def scan_global_library(
        self,
        library_path: str | Path = None,
        authors: List[str] = None,
        chunk_size: int = 500,
        max_chunks: int = 200,
        skip_errors: bool = True
    ) -> Dict[str, Any]:
        """
        扫描整个全局资料库（按作家子文件夹）

        Args:
            library_path: 资料库路径，默认使用全局配置
            authors: 指定要导入的作家列表，None表示全部
            chunk_size: 分块大小
            max_chunks: 每个文件的最大块数
            skip_errors: 是否跳过错误

        Returns:
            导入结果统计

        Example:
            # 导入所有作家
            result = rag.scan_global_library()

            # 只导入指定作家
            result = rag.scan_global_library(authors=["马尔克斯", "余华"])
        """
        lib_path = Path(library_path) if library_path else get_global_library_path()

        if not lib_path.exists():
            raise StyleRAGError(
                f"全局资料库不存在: {lib_path}\n"
                f"请创建目录并按作家名创建子文件夹存放参考小说。"
            )

        # 获取所有作家
        available_authors = self.list_global_authors(lib_path)

        if not available_authors:
            raise StyleRAGError(
                f"资料库为空: {lib_path}\n"
                f"请按以下结构组织:\n"
                f"  {lib_path}/\n"
                f"    ├── 作家名1/\n"
                f"    │   ├── 小说1.txt\n"
                f"    │   └── 小说2.epub\n"
                f"    └── 作家名2/\n"
                f"        └── 小说.pdf"
            )

        # 过滤指定作家
        if authors:
            target_authors = [a for a in available_authors if a["name"] in authors]
            not_found = set(authors) - {a["name"] for a in target_authors}
            if not_found:
                raise StyleRAGError(f"未找到作家: {', '.join(not_found)}")
        else:
            target_authors = available_authors

        results = {
            "library_path": str(lib_path),
            "authors_processed": [],
            "total_success": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "details": {}
        }

        for author_info in target_authors:
            author_name = author_info["name"]
            try:
                author_result = self.scan_author(
                    author_name=author_name,
                    library_path=lib_path,
                    chunk_size=chunk_size,
                    max_chunks=max_chunks,
                    skip_errors=skip_errors
                )

                results["authors_processed"].append(author_name)
                results["total_success"] += author_result["success_count"]
                results["total_failed"] += author_result["failed_count"]
                results["total_skipped"] += author_result["skipped_count"]
                results["details"][author_name] = author_result

            except Exception as e:
                if not skip_errors:
                    raise
                results["details"][author_name] = {"error": str(e)}

        return results

    def list_imported_authors(self) -> List[str]:
        """
        列出已导入的所有作家

        Returns:
            作家名列表
        """
        authors = set()
        for ref_info in self.metadata["references"].values():
            author = ref_info.get("author")
            if author and author != "Unknown":
                authors.add(author)
        return sorted(list(authors))

    def retrieve_by_author(
        self,
        query: str,
        author: str,
        n_results: int = 3,
        chunk_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索指定作家的风格样本

        Args:
            query: 查询文本
            author: 作家名
            n_results: 返回结果数量
            chunk_type: 块类型过滤

        Returns:
            样本列表
        """
        # 构建过滤条件（ChromaDB 需要 $and 组合多条件）
        if chunk_type:
            where = {
                "$and": [
                    {"author": {"$eq": author}},
                    {"chunk_type": {"$eq": chunk_type}}
                ]
            }
        else:
            where = {"author": {"$eq": author}}

        # 使用自定义模型生成查询向量
        query_embedding = self.model.encode([query]).tolist()

        # 检索
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where
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

    def get_style_context_by_author(
        self,
        scene_description: str,
        author: str,
        scene_type: Optional[str] = None,
        n_samples: int = 3
    ) -> Dict[str, Any]:
        """
        获取指定作家风格的上下文

        Args:
            scene_description: 场景描述
            author: 作家名
            scene_type: 场景类型
            n_samples: 样本数量

        Returns:
            风格上下文
        """
        # 映射场景类型
        type_mapping = {
            "dialogue": "dialogue",
            "action": "action",
            "narrative": "description",
            "description": "description"
        }
        chunk_type = type_mapping.get(scene_type)

        samples = self.retrieve_by_author(
            query=scene_description,
            author=author,
            n_results=n_samples,
            chunk_type=chunk_type
        )

        return {
            "author": author,
            "samples": samples,
            "sample_count": len(samples)
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


def check_file_parser_dependencies() -> Dict[str, bool]:
    """
    检查文件解析依赖是否已安装

    Returns:
        依赖状态字典
    """
    return {
        "txt": True,  # 内置支持
        "pdf": PYPDF2_AVAILABLE,
        "epub": EBOOKLIB_AVAILABLE and BS4_AVAILABLE,
        "ebooklib": EBOOKLIB_AVAILABLE,
        "beautifulsoup4": BS4_AVAILABLE,
        "PyPDF2": PYPDF2_AVAILABLE
    }


def install_instructions() -> str:
    """返回依赖安装说明"""
    return """
RAG风格系统依赖安装：

【核心依赖（必需）】
pip install chromadb sentence-transformers

【文件格式支持（可选）】
pip install PyPDF2              # PDF支持
pip install ebooklib beautifulsoup4  # EPUB支持

【一次性安装所有】
pip install chromadb sentence-transformers PyPDF2 ebooklib beautifulsoup4

注意：
- sentence-transformers需要PyTorch，如果未安装会自动安装
- 首次运行会下载embedding模型（约400MB），请确保网络连接正常
- TXT格式无需额外依赖，支持多种编码自动检测
"""
