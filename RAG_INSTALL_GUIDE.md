# RAG系统安装指南

## ⚠️ Python 3.14 兼容性问题

**当前问题**：
- ChromaDB需要 `numpy < 2.0`
- Python 3.14 只有 `numpy >= 2.3` 的预编译包
- 编译numpy 1.x需要C/C++编译器

## 🔧 解决方案

### 方案1: 使用Python 3.11或3.12（推荐）⭐⭐⭐⭐⭐

**最简单可靠的方案**：

```bash
# 1. 下载并安装Python 3.12
# https://www.python.org/downloads/release/python-3120/

# 2. 使用Python 3.12创建虚拟环境
python3.12 -m venv venv_rag
venv_rag\Scripts\activate  # Windows
# source venv_rag/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install chromadb sentence-transformers

# 4. 测试
python -c "from style_rag import check_dependencies; print(check_dependencies())"
```

**优点**：
- ✅ 100%兼容，无需编译
- ✅ 安装快速（预编译wheel）
- ✅ 稳定可靠

---

### 方案2: 安装Visual Studio Build Tools ⭐⭐⭐

如果坚持使用Python 3.14，需要安装编译工具：

**步骤**：

1. **下载Visual Studio Build Tools**:
   - 访问: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - 下载 "Build Tools for Visual Studio 2022"

2. **安装C++组件**:
   - 运行安装程序
   - 勾选 "Desktop development with C++"
   - 安装大小约 7GB

3. **重新尝试安装**:
   ```bash
   pip install chromadb sentence-transformers
   ```

**缺点**：
- ❌ 安装包很大（7GB+）
- ❌ 安装时间长（30分钟+）
- ❌ 编译耗时

---

### 方案3: 使用替代向量数据库 ⭐⭐⭐⭐

使用 **FAISS**（Facebook AI Similarity Search）替代ChromaDB：

```bash
pip install faiss-cpu sentence-transformers
```

**需要修改代码**：
```python
# 将在style_rag.py中使用FAISS替代ChromaDB
# 优点：更快、更轻量、兼容numpy 2.x
# 缺点：需要修改代码实现
```

---

### 方案4: 等待ChromaDB更新 ⭐⭐

ChromaDB团队正在开发numpy 2.x兼容版本。

**追踪进度**：
- GitHub Issue: https://github.com/chroma-core/chroma/issues/3026

预计2025年Q1发布兼容版本。

---

## 📊 方案对比

| 方案 | 难度 | 成功率 | 时间成本 | 推荐度 |
|------|-----|--------|---------|--------|
| Python 3.12 | 简单 | 100% | 10分钟 | ⭐⭐⭐⭐⭐ |
| VS Build Tools | 中等 | 95% | 1小时 | ⭐⭐⭐ |
| FAISS替代 | 困难 | 90% | 2小时 | ⭐⭐⭐⭐ |
| 等待更新 | 无 | - | 1-3个月 | ⭐⭐ |

---

## 🎯 推荐行动

**对于大多数用户**：

```bash
# 1. 下载Python 3.12
# https://www.python.org/downloads/release/python-3120/

# 2. 创建独立环境
python3.12 -m venv snowflake_rag
snowflake_rag\Scripts\activate

# 3. 安装依赖
pip install chromadb sentence-transformers

# 4. 运行Snowflake Writer
cd snowflake-writer
python -c "from story_engine import *; print('✅ RAG系统就绪')"
```

---

## ❓ 常见问题

### Q: 我必须降级Python吗？

A: 不是必须，但这是最简单的方案。你可以保留Python 3.14做其他工作，只在RAG项目中使用Python 3.12虚拟环境。

### Q: 虚拟环境会影响其他项目吗？

A: 不会。虚拟环境是隔离的，不影响全局Python安装。

### Q: FAISS和ChromaDB有什么区别？

A:
- **FAISS**: 更快、更轻量，但功能较少
- **ChromaDB**: 功能更丰富、持久化存储、更易用

### Q: 什么时候ChromaDB会支持numpy 2.x？

A: 官方正在开发中，预计2025年Q1-Q2发布。

---

## 🔄 临时解决方案（无需安装依赖）

如果暂时无法安装依赖，可以使用**轻量级风格指南**替代RAG：

**编辑metadata.json添加风格指南**：

```json
{
  "title": "我的小说",
  "style_guide": {
    "reference_work": "《余华-活着》",
    "sentence_style": "简短有力，口语化",
    "vocabulary": "朴实、生活化词汇",
    "pacing": "克制、缓慢积累情感",
    "dialogue_style": "简洁、富有张力",
    "key_phrases": [
      "人活着，就得往前看",
      "日子还得过下去"
    ]
  }
}
```

**在Step 10时手动引用**风格指南即可。

---

## 📞 需要帮助？

如果遇到问题：

1. **检查Python版本**:
   ```bash
   python --version
   ```

2. **查看已安装包**:
   ```bash
   pip list | grep -E "numpy|chromadb|sentence"
   ```

3. **创建Issue报告**:
   提供上述命令的输出

---

**建议**：使用Python 3.12是最快最可靠的方案 🎯
