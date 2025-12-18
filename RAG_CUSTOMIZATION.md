# RAG系统自定义指南

## 📍 数据库存储位置

### 默认存储结构

```
snowflake_projects/my_novel/
├── .chroma/                    # ChromaDB向量数据库
│   ├── chroma.sqlite3         # SQLite索引
│   ├── [UUID]/                # 向量数据分片
│   └── ...
├── style_references/
│   └── metadata.json           # 参考小说元数据
└── [其他项目文件]
```

**存储位置**：
- **ChromaDB**: `项目目录/.chroma/`
- **元数据**: `项目目录/style_references/metadata.json`
- **每个项目独立存储**，互不干扰

### 数据库来源

1. **自动创建**: 首次调用`enable_style_rag()`时自动创建
2. **持久化存储**: 数据保存在本地磁盘，重启后仍可用
3. **项目隔离**: 每个小说项目有独立的数据库

---

## 🎨 自定义选项

### 1. 自定义Embedding模型

当前使用的是 `paraphrase-MiniLM-L6-v2`（英文优化，90MB）

**更换为其他模型**：

编辑 `style_rag.py` 第89行：

```python
# 默认（英文优化）
self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# 更换为多语言模型（中文效果更好）
self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 更换为中文专用模型
self.model = SentenceTransformer('shibing624/text2vec-base-chinese')

# 使用更大的模型（效果更好但更慢）
self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
```

**推荐模型对比**：

| 模型 | 语言 | 大小 | 速度 | 质量 | 推荐度 |
|------|-----|------|------|------|-------|
| `paraphrase-MiniLM-L6-v2` | 英文 | 90MB | 快 | 中 | ⭐⭐⭐ |
| `paraphrase-multilingual-MiniLM-L12-v2` | 多语言 | 470MB | 中 | 高 | ⭐⭐⭐⭐⭐ |
| `shibing624/text2vec-base-chinese` | 中文 | 400MB | 中 | 高 | ⭐⭐⭐⭐⭐ |
| `all-mpnet-base-v2` | 英文 | 420MB | 慢 | 很高 | ⭐⭐⭐⭐ |

**如何更换模型**：

```python
# 方法1: 修改源码（永久生效）
# 编辑 style_rag.py 第89行

# 方法2: 继承并覆盖（不修改源码）
from style_rag import StyleRAG
from sentence_transformers import SentenceTransformer

class CustomStyleRAG(StyleRAG):
    def __init__(self, project_path):
        super().__init__(project_path)
        # 覆盖模型
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
```

---

### 2. 自定义数据库位置

**默认行为**：数据库存储在项目目录下

**自定义路径**：

```python
# 修改 style_rag.py 第75行

# 默认（项目目录下）
chroma_path = project_path / ".chroma"

# 自定义为全局共享位置
chroma_path = Path.home() / ".snowflake_rag_global" / project_path.name

# 自定义为外部驱动器（大容量存储）
chroma_path = Path("D:/RAG_Storage") / project_path.name

# 自定义为内存数据库（重启后丢失，适合测试）
# 注意：需要改用 Client() 而非 PersistentClient()
```

**实现全局共享数据库**：

```python
# 在 style_rag.py 的 __init__ 方法中修改：

# 全局共享模式（所有项目共用同一个数据库）
self.global_mode = True  # 新增配置项

if self.global_mode:
    # 全局数据库路径
    chroma_path = Path.home() / ".snowflake_rag_shared"
    collection_name = f"project_{project_path.name}"
else:
    # 项目独立数据库（默认）
    chroma_path = project_path / ".chroma"
    collection_name = "style_references"

self.client = chromadb.PersistentClient(
    path=str(chroma_path),
    settings=Settings(anonymized_telemetry=False)
)

self.collection = self.client.get_or_create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"}
)
```

**优缺点对比**：

| 模式 | 优点 | 缺点 | 适用场景 |
|------|-----|------|---------|
| **项目独立** | 数据隔离、易管理 | 重复存储相同参考 | 默认推荐 |
| **全局共享** | 节省空间、参考复用 | 多项目冲突风险 | 多项目使用相同参考 |
| **外部驱动** | 不占C盘空间 | 需要手动路径配置 | 大量参考小说 |

---

### 3. 自定义相似度算法

**默认使用**: 余弦相似度 (`cosine`)

**更换为其他算法**：

编辑 `style_rag.py` 第84行：

```python
# 默认（余弦相似度）
metadata={"hnsw:space": "cosine"}

# 更换为欧几里得距离
metadata={"hnsw:space": "l2"}

# 更换为内积
metadata={"hnsw:space": "ip"}
```

**算法对比**：

| 算法 | 特点 | 适用场景 |
|------|-----|---------|
| `cosine` | 关注方向相似性 | **推荐**，适合文本语义 |
| `l2` | 关注绝对距离 | 长度敏感的匹配 |
| `ip` | 关注内积大小 | 向量已归一化时使用 |

---

### 4. 自定义分块策略

**默认配置**：
- 块大小：500字符
- 最大块数：100个

**自定义分块参数**：

```python
from story_engine import get_engine

engine = get_engine()

# 方法1: 调用时指定
result = engine.add_style_reference(
    title="参考小说",
    content=content,
    chunk_size=800,      # 更大的块（更多上下文）
    max_chunks=200       # 允许更多块
)

# 方法2: 修改默认值（编辑style_rag.py）
def add_reference_novel(
    self,
    title: str,
    content: str,
    author: str = None,
    chunk_size: int = 800,  # ← 修改这里
    max_chunks: int = 200   # ← 修改这里
):
```

**分块大小建议**：

| 块大小 | 适用场景 | Token消耗 | 上下文完整性 |
|--------|---------|-----------|-------------|
| 300字符 | 快速匹配、降低成本 | 低 | 较差 |
| 500字符 | **默认推荐** | 中 | 良好 |
| 800字符 | 长篇叙述、复杂风格 | 高 | 优秀 |
| 1000+字符 | 学术写作、特殊需求 | 很高 | 很好 |

---

### 5. 自定义场景类型分类

**默认分类逻辑** (style_rag.py 第120-136行)：

```python
def _classify_chunk_type(self, text: str) -> str:
    """简单的块类型分类"""
    dialogue_markers = text.count('"') + text.count('"') + text.count('"')
    dialogue_ratio = dialogue_markers / max(len(text), 1)

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
```

**增强分类逻辑**：

```python
def _classify_chunk_type(self, text: str) -> str:
    """增强的块类型分类"""

    # 1. 对话检测（更精确）
    dialogue_patterns = ['"', '"', '"', '「', '」', '说', '道', '问', '答']
    dialogue_score = sum(text.count(p) for p in dialogue_patterns)
    dialogue_ratio = dialogue_score / max(len(text), 1)

    # 2. 动作检测（扩展动词库）
    action_verbs = [
        '跑', '走', '打', '踢', '跳', '冲', '扑', '抓', '推', '拉',
        '击', '刺', '砍', '劈', '挡', '闪', '躲', '转', '旋', '飞'
    ]
    action_count = sum(text.count(verb) for verb in action_verbs)

    # 3. 心理描写检测
    psychological_words = ['想', '觉得', '感到', '认为', '心里', '思考']
    psych_count = sum(text.count(word) for word in psychological_words)

    # 4. 环境描写检测
    environment_words = ['天空', '阳光', '树木', '房间', '街道', '风景']
    env_count = sum(text.count(word) for word in environment_words)

    # 分类决策树
    if dialogue_ratio > 0.15:
        return 'dialogue'
    elif action_count > 5:
        return 'action'
    elif psych_count > 3:
        return 'psychological'  # 新增类型
    elif env_count > 2:
        return 'environment'     # 新增类型
    elif len(text) > 300:
        return 'narrative'
    else:
        return 'mixed'
```

**注意**: 新增类型后，检索时也需要相应调整 `get_style_context()` 的 `type_mapping`。

---

### 6. 自定义检索策略

**默认行为**: 返回前N个最相似的样本

**自定义检索逻辑**：

```python
# 在 style_rag.py 的 retrieve_style_samples 方法中自定义

def retrieve_style_samples(
    self,
    query: str,
    n_results: int = 3,
    chunk_type: Optional[str] = None,
    ref_id: Optional[str] = None,
    min_similarity: float = 0.7  # 新增：最小相似度阈值
) -> List[Dict[str, Any]]:
    """检索相似的风格样本"""

    # 标准检索
    results = self.collection.query(
        query_texts=[query],
        n_results=n_results * 2,  # 多检索一些候选
        where=where if where else None
    )

    # 过滤低相似度样本
    filtered_samples = []
    for i in range(len(results["documents"][0])):
        similarity = 1 - results["distances"][0][i]  # 转换为相似度

        if similarity >= min_similarity:
            filtered_samples.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "similarity": similarity
            })

    # 只返回前n_results个
    return filtered_samples[:n_results]
```

**高级检索策略**：

```python
# 多样性采样（避免返回过于相似的样本）
def retrieve_diverse_samples(self, query: str, n_results: int = 3):
    """检索多样化的样本"""

    # 1. 先检索较多候选
    candidates = self.collection.query(
        query_texts=[query],
        n_results=n_results * 5
    )

    # 2. 多样性过滤（简单实现：按字符长度分组）
    short = []  # < 300字符
    medium = []  # 300-600
    long = []   # > 600

    for i, text in enumerate(candidates["documents"][0]):
        length = len(text)
        sample = {
            "text": text,
            "metadata": candidates["metadatas"][0][i],
            "distance": candidates["distances"][0][i]
        }

        if length < 300:
            short.append(sample)
        elif length < 600:
            medium.append(sample)
        else:
            long.append(sample)

    # 3. 平衡选择
    results = []
    for group in [medium, short, long]:  # 优先中等长度
        results.extend(group[:n_results - len(results)])
        if len(results) >= n_results:
            break

    return results[:n_results]
```

---

## 🔧 高级自定义案例

### 案例1: 使用中文优化模型

```python
# 1. 修改 style_rag.py 第89行
self.model = SentenceTransformer('shibing624/text2vec-base-chinese')

# 2. 首次运行会自动下载中文模型（400MB）

# 3. 使用
add_style_reference("余华-活着", content, "余华")
# 中文语义理解更准确
```

### 案例2: 全局共享参考库

```python
# 修改 style_rag.py __init__ 方法

def __init__(self, project_path: Path, shared_mode: bool = False):
    self.project_path = project_path
    self.shared_mode = shared_mode

    if shared_mode:
        # 所有项目共享同一个数据库
        chroma_path = Path.home() / ".snowflake_rag_global"
        collection_name = "shared_style_references"
    else:
        # 项目独立
        chroma_path = project_path / ".chroma"
        collection_name = "style_references"

    # 其余代码不变...
```

### 案例3: 外部API替代Sentence Transformers

```python
# 如果想用OpenAI/Anthropic的embedding API

import requests

class APIStyleRAG(StyleRAG):
    def __init__(self, project_path: Path):
        super().__init__(project_path)
        self.api_key = "your_api_key"
        self.model = None  # 不用本地模型

    def _get_embedding(self, text: str):
        """调用外部API获取embedding"""
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "input": text,
                "model": "text-embedding-3-small"
            }
        )
        return response.json()["data"][0]["embedding"]

    def add_reference_novel(self, title, content, ...):
        # 修改为使用 self._get_embedding() 而非 self.model.encode()
        ...
```

---

## 📊 性能优化建议

### 1. 数据库大小控制

```python
# 限制总块数
max_total_chunks = 500  # 全局上限

# 添加前检查
stats = engine.get_rag_statistics()
if stats['total_chunks'] >= max_total_chunks:
    # 删除旧的参考或提示用户
    pass
```

### 2. 批量操作优化

```python
# 批量添加参考
references = [
    ("小说1", content1, "作者1"),
    ("小说2", content2, "作者2"),
    ("小说3", content3, "作者3"),
]

for title, content, author in references:
    add_style_reference(title, content, author)
```

### 3. 缓存Embedding结果

```python
# 如果同一个场景会多次检索，可以缓存embedding
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_embedding(text: str):
    return model.encode([text])[0]
```

---

## 🚨 注意事项

1. **模型更换**: 更换embedding模型后，需要重新添加所有参考小说
2. **数据库迁移**: 更改数据库路径后，旧数据不会自动迁移
3. **版本兼容**: ChromaDB版本升级可能导致数据不兼容
4. **隐私保护**: 自定义路径时注意不要将数据库提交到版本控制

---

## 📖 完整示例

```python
# 自定义配置的完整流程

# 1. 修改 style_rag.py（可选）
# 2. 初始化项目
from story_engine import *

init_project("我的小说")

# 3. 启用RAG并验证
result = enable_style_rag()
print(f"数据库位置: {result}")

# 4. 添加参考（使用自定义参数）
engine = get_engine()
result = engine.add_style_reference(
    title="参考小说",
    content=novel_content,
    author="作者名",
    chunk_size=800,      # 自定义块大小
    max_chunks=150       # 自定义最大块数
)

# 5. 检索时指定参数
samples = engine.get_style_context_for_scene(
    scene_description="场景描述",
    scene_type="narrative",
    n_samples=5  # 自定义样本数
)

# 6. 查看统计
stats = engine.get_rag_statistics()
print(f"数据库统计: {stats}")
```

---

希望这份自定义指南能帮助你根据需求调整RAG系统！🎨
