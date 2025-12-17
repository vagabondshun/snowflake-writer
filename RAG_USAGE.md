# RAG风格模仿系统 - 使用指南

## 📖 功能简介

RAG（Retrieval-Augmented Generation）风格系统让你的小说能够模仿特定参考作品的写作风格。

**核心特性**：
- 🎨 自动学习参考小说的写作风格
- 🔍 智能检索相似场景的风格样本
- 💡 为Step 10草稿生成提供风格指导
- 📊 向量检索确保风格一致性

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd snowflake-writer
pip install chromadb sentence-transformers
```

**注意**：
- 首次安装会下载PyTorch（约1GB）
- 首次运行会下载embedding模型（约90MB）
- 需要良好的网络连接

### 2. 基础使用

```python
import sys
sys.path.insert(0, 'snowflake-writer')

from story_engine import *

# 1. 初始化项目
init_project("我的小说")

# 2. 启用RAG系统
result = enable_style_rag()
print(f"RAG已启用: {result}")

# 3. 添加参考小说
with open('reference_novel.txt', 'r', encoding='utf-8') as f:
    content = f.read()

result = add_style_reference(
    title="百年孤独",
    content=content,
    author="加西亚·马尔克斯"
)

print(f"已添加: {result['chunks_added']} 个文本块")

# 4. 查看已添加的参考
references = list_style_references()
for ref in references:
    print(f"- {ref['title']} by {ref['author']}")

# 5. 在写作时获取风格样本（Agent-Epsilon会自动调用）
engine = get_engine()
samples = engine.get_style_context_for_scene(
    scene_description="主角在雨夜中独自徘徊，思考命运",
    scene_type="narrative",
    n_samples=3
)

if samples:
    print(f"\n找到 {samples['sample_count']} 个相似样本：")
    for i, sample in enumerate(samples['samples'], 1):
        print(f"\n样本 {i}:")
        print(f"  来源: {sample['metadata']['title']}")
        print(f"  类型: {sample['metadata']['chunk_type']}")
        print(f"  相似度: {1 - sample['distance']:.2%}")
        print(f"  内容: {sample['text'][:100]}...")
```

---

## 💻 完整API参考

### 启用和管理

#### `enable_style_rag()`
启用RAG风格系统

```python
result = enable_style_rag()
# 返回: {'enabled': True, 'statistics': {...}}
```

#### `is_style_rag_enabled()`
检查RAG系统是否已启用

```python
if is_style_rag_enabled():
    print("RAG系统已启用")
```

#### `get_rag_statistics()`
获取RAG系统统计信息

```python
stats = get_rag_statistics()
print(f"已添加 {stats['reference_count']} 部参考小说")
print(f"总计 {stats['total_chunks']} 个文本块")
```

---

### 添加和管理参考小说

#### `add_style_reference(title, content, author=None)`
添加参考小说

```python
with open('novel.txt', 'r', encoding='utf-8') as f:
    content = f.read()

result = add_style_reference(
    title="小说标题",
    content=content,
    author="作者名"
)

# 返回:
# {
#     'ref_id': 'abc123',
#     'title': '小说标题',
#     'chunks_added': 85,
#     'total_chars': 42500
# }
```

**参数说明**：
- `title`: 小说标题（必需）
- `content`: 小说全文（必需）
- `author`: 作者名（可选）

**自动处理**：
- 智能文本分块（默认500字符/块）
- 自动向量化
- 场景类型分类（对话/动作/叙述）

#### `list_style_references()`
列出所有参考小说

```python
refs = list_style_references()
for ref in refs:
    print(f"{ref['title']} ({ref['chunk_count']} 块)")
```

#### `remove_style_reference(ref_id)`
删除指定参考小说

```python
success = remove_style_reference('abc123')
if success:
    print("删除成功")
```

---

### 检索风格样本

#### `engine.get_style_context_for_scene()`
为场景获取风格上下文

```python
engine = get_engine()

context = engine.get_style_context_for_scene(
    scene_description="当前场景的描述或大纲",
    scene_type="narrative",  # 'dialogue', 'action', 'narrative'
    n_samples=3              # 返回样本数量
)

if context:
    for sample in context['samples']:
        print(f"参考: {sample['text'][:200]}...")
```

**场景类型**：
- `dialogue` - 对话场景
- `action` - 动作场景
- `narrative` - 叙述/描写场景
- `None` - 自动匹配

---

## 🎯 实战示例

### 示例1: 模仿马尔克斯的魔幻现实主义风格

```python
# 准备参考小说
garcia_marquez = """
多年以后，面对行刑队，奥雷里亚诺·布恩迪亚上校将会回想起，
他父亲带他去见识冰块的那个遥远的下午。那时的马孔多是一个
二十户人家的村落，土屋就盖在河岸上，河水清澈，沿着遍布石头
的河床流去，河里的石头光滑、雪白，活像史前的巨蛋...
"""

# 添加参考
add_style_reference(
    title="百年孤独节选",
    content=garcia_marquez,
    author="加西亚·马尔克斯"
)

# 写作时获取风格指导
samples = engine.get_style_context_for_scene(
    scene_description="主角回忆童年时光",
    scene_type="narrative",
    n_samples=2
)

# Agent-Epsilon会将这些样本注入到生成prompt中
# 生成的文本会模仿马尔克斯的长句、时间倒叙、细节描写风格
```

### 示例2: 模仿现代都市小说风格

```python
# 准备参考
urban_novel = """
"你疯了吗？"林晓的声音在电话里尖锐刺耳。

我看着窗外的车流，平静地说："没有。我只是想清楚了。"

三秒钟的沉默。

"那你想清楚了什么？"她问，声音软了下来。

我关掉手机，把它扔进抽屉。这座城市每天都在制造答案，
但从来不给人提问的机会...
"""

add_style_reference(
    title="都市小说风格样本",
    content=urban_novel
)

# 检索对话场景样本
samples = engine.get_style_context_for_scene(
    scene_description="男女主角的电话对话",
    scene_type="dialogue",
    n_samples=3
)

# 生成的对话会模仿：简短句式、快节奏、现代语感
```

### 示例3: 混合多种风格

```python
# 可以同时添加多个参考
add_style_reference("参考小说A", content_a, "作者A")
add_style_reference("参考小说B", content_b, "作者B")

# RAG系统会自动找到最相关的样本
# 可以在不同场景中自然切换风格
```

---

## 📊 Token消耗估算

| 样本数量 | 每样本字符数 | Token增加 | 成本影响 |
|---------|------------|----------|---------|
| 1个样本 | ~500字符 | ~600 tokens | $0.0018 |
| 3个样本 | ~1500字符 | ~1800 tokens | $0.0054 |
| 5个样本 | ~2500字符 | ~3000 tokens | $0.009 |

**优化建议**：
- 普通场景：1-2个样本
- 关键场景：3-5个样本
- 60个场景的小说，平均3样本：~$0.32 USD

---

## 🔧 高级配置

### 自定义分块参数

```python
engine = get_engine()

# 更大的块（更多上下文，但token消耗更高）
engine.add_style_reference(
    title="长篇参考",
    content=content,
    chunk_size=800,  # 默认500
    max_chunks=150   # 默认100
)

# 更小的块（更精准匹配，但可能缺乏上下文）
engine.add_style_reference(
    title="短篇参考",
    content=content,
    chunk_size=300
)
```

### 按类型检索

```python
# 只检索对话样本
dialogue_samples = engine._style_rag.retrieve_style_samples(
    query="场景描述",
    n_results=3,
    chunk_type="dialogue"
)

# 只检索特定参考小说
specific_samples = engine._style_rag.retrieve_style_samples(
    query="场景描述",
    n_results=3,
    ref_id="abc123"  # 特定参考的ID
)
```

---

## 🚨 常见问题

### Q: 依赖安装失败怎么办？

A: 分步安装：
```bash
pip install torch  # 先安装PyTorch
pip install chromadb
pip install sentence-transformers
```

### Q: 首次运行很慢？

A: 正常现象，首次运行会下载embedding模型（90MB），后续运行会使用缓存。

### Q: 可以使用版权作品作为参考吗？

A: **仅供学习和个人使用**。如果要商业发布，请：
- 只学习风格特征，不要直接抄袭
- 确保生成内容完全原创
- 考虑咨询法律意见

### Q: 如何选择好的参考小说？

A: 建议：
- 选择风格鲜明的作品
- 选择与你小说类型相近的
- 可以混合多部作品
- 节选精华部分（无需整本小说）

### Q: RAG会让所有场景风格一样吗？

A: 不会，RAG会根据每个场景的内容检索最相似的样本，自然形成风格变化。

### Q: 如何查看使用了哪些样本？

A:
```python
# 开启调试模式查看
samples = engine.get_style_context_for_scene(...)
for s in samples['samples']:
    print(f"使用样本: {s['metadata']['title']}")
    print(f"相似度: {1 - s['distance']:.2%}")
```

---

## 🎓 最佳实践

### 1. 参考小说选择策略

```python
# ✅ 推荐：选择风格化文本
add_style_reference("诗意叙述", poetic_content)

# ❌ 避免：技术文档、新闻报道等非文学文本
```

### 2. 渐进式使用

```python
# Step 1-8: 不使用RAG（节省成本）
# Step 9: 启用RAG，规划场景时建立风格意识
# Step 10: 草稿生成时充分利用RAG
```

### 3. 分场景优化

```python
# 高潮场景：多样本，高质量
climax_samples = engine.get_style_context_for_scene(
    description="高潮对决",
    n_samples=5
)

# 过渡场景：少样本，控制成本
transition_samples = engine.get_style_context_for_scene(
    description="日常对话",
    n_samples=1
)
```

---

## 📈 效果对比

### 不使用RAG
```
"我很难过，"他说。他看着窗外。天气很好。
```

### 使用RAG（模仿村上春树）
```
"这种难过，就像冰箱里被遗忘的啤酒，"他说，
视线越过我的肩膀，落在窗外那片过分湛蓝的天空上。
```

### 使用RAG（模仿金庸）
```
他叹了口气，黯然道："难过有什么用？"
转身望向窗外，但见远山如黛，白云悠悠。
```

---

## 🎯 总结

RAG风格系统提供：
- ✅ 自动化风格学习
- ✅ 精准场景匹配
- ✅ 灵活成本控制
- ✅ 多风格融合

**建议起步**：
1. 选择1-2部风格鲜明的小说作为参考
2. 先在几个场景中测试效果
3. 根据结果调整样本数量和参考选择

享受AI辅助创作的乐趣！ 🎨✨
