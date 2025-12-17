# Snowflake Writer - Changelog

## Version 1.5 - 2024-12-17

### 🎨 RAG风格模仿系统

这是一个专注于**写作风格增强**的版本，添加了完整的RAG（检索增强生成）系统，让你的小说能够模仿参考作品的写作风格。

#### 1. RAG系统架构 🚀

**核心组件**:
- **ChromaDB** - 向量数据库，持久化存储
- **Sentence Transformers** - 文本向量化（使用paraphrase-MiniLM-L6-v2模型）
- **智能检索** - 基于余弦相似度的语义搜索

**工作流程**:
```
参考小说 → 智能分块 → 向量化 → 存储到ChromaDB
                                    ↓
当前场景 → 向量化 → 相似度检索 ← 返回最相关样本 → 注入到生成prompt
```

#### 2. 核心功能 🎯

**新增模块**: `style_rag.py` (450行代码)

**功能特性**:
- ✅ 自动文本分块（智能段落识别）
- ✅ 场景类型分类（对话/动作/叙述/混合）
- ✅ 向量相似度检索
- ✅ 批量参考管理
- ✅ 延迟加载（不使用时零开销）

**分块策略**:
```python
# 默认500字符/块，按段落边界智能分割
# 自动分类块类型（对话、动作、叙述）
# 支持自定义分块大小和最大块数
```

#### 3. API接口 🛠️

**Engine集成**:
```python
# 启用RAG系统
enable_style_rag() -> Dict

# 添加参考小说
add_style_reference(title, content, author=None) -> Dict

# 列出所有参考
list_style_references() -> List[Dict]

# 删除参考
remove_style_reference(ref_id) -> bool

# 获取场景风格样本
get_style_context_for_scene(description, scene_type, n_samples) -> Dict

# 统计信息
get_rag_statistics() -> Dict
```

**StyleRAG类方法**:
```python
class StyleRAG:
    - add_reference_novel()      # 添加参考小说
    - retrieve_style_samples()   # 检索相似样本
    - get_style_context()        # 获取完整上下文
    - list_references()          # 列出所有参考
    - remove_reference()         # 删除参考
    - clear_all_references()     # 清空所有参考
    - get_statistics()           # 获取统计信息
```

#### 4. 智能特性 ✨

**场景类型匹配**:
- `dialogue` - 优先检索对话场景
- `action` - 优先检索动作场景
- `narrative` - 优先检索叙述场景
- `None` - 自动匹配最相似内容

**自动分类逻辑**:
```python
# 基于内容特征自动识别：
- 对话标记密度（引号）
- 动作动词频率
- 文本长度
```

#### 5. Token消耗分析 💰

| 样本数 | 字符数 | Token增加 | 成本(Sonnet) |
|--------|--------|----------|--------------|
| 1个样本 | ~500 | +600 | $0.0018 |
| 3个样本 | ~1500 | +1800 | $0.0054 |
| 5个样本 | ~2500 | +3000 | $0.009 |

**实际项目成本**:
- 60场景小说，每场景3样本：$0.32 USD
- 100场景小说，每场景3样本：$0.54 USD

**优化策略**:
- 关键场景：3-5样本
- 普通场景：1-2样本
- 过渡场景：0-1样本

#### 6. 文档和测试 📚

**新增文档**:
- `RAG_USAGE.md` - 完整使用指南（600+行）
- `requirements.txt` - 依赖说明

**新增测试**:
- `tests/test_style_rag.py` - 13个RAG专项测试
- 测试覆盖：初始化、分块、分类、检索、管理

**更新文档**:
- `README.md` - 添加RAG章节和快速入门
- `.gitignore` - 排除.chroma/和style_references/

#### 7. 使用示例 🎓

**基础用法**:
```python
from story_engine import *

# 初始化并启用RAG
init_project("我的小说")
enable_style_rag()

# 添加参考小说
with open('百年孤独.txt', 'r', encoding='utf-8') as f:
    content = f.read()

add_style_reference(
    title="百年孤独",
    content=content,
    author="加西亚·马尔克斯"
)

# 获取风格样本（Agent-Epsilon自动调用）
engine = get_engine()
samples = engine.get_style_context_for_scene(
    scene_description="主角回忆童年",
    scene_type="narrative",
    n_samples=3
)
```

**效果对比**:
```
# 不使用RAG
"我很难过，"他说。他看着窗外。天气很好。

# 使用RAG（模仿村上春树）
"这种难过，就像冰箱里被遗忘的啤酒，"他说，
视线越过我的肩膀，落在窗外那片过分湛蓝的天空上。
```

#### 8. 依赖管理 📦

**可选依赖**（仅RAG功能需要）:
```bash
pip install chromadb sentence-transformers
```

**首次运行**:
- 下载embedding模型（~90MB）
- 需要网络连接
- 后续运行使用本地缓存

**向后兼容**:
- RAG系统完全可选
- 不安装依赖不影响其他功能
- 延迟加载，不使用时零开销

#### 9. 数据存储 💾

**项目结构**:
```
my_novel/
├── .chroma/                    # ChromaDB数据库
│   └── [向量数据文件]
├── style_references/
│   └── metadata.json           # 参考小说元数据
```

**隐私保护**:
- .chroma/ 和 style_references/ 已加入.gitignore
- 参考小说数据仅本地存储
- 不会上传到版本控制

#### 10. 性能特性 ⚡

**向量检索性能**:
- 单次检索：< 100ms
- 支持批量检索
- HNSW索引优化

**存储效率**:
- 100块文本：~5MB数据库大小
- 自动压缩和索引
- 支持增量更新

---

## Version 1.4 - 2024-12-17

### ⚡ 性能优化 - 智能缓存系统

这是一个专注于**性能提升**的版本，添加了智能缓存机制以减少重复文件读取操作。

#### 1. 缓存系统架构 🚀

**缓存存储**:
```python
self._cache = {
    "step_outputs": {},      # {step_number: content}
    "characters": None,      # List of all characters
    "scene_list": None,      # Scene list
    "metadata": None         # Project metadata
}
```

**缓存统计**:
```python
stats = engine.get_cache_stats()
# 返回: {
#   "hits": 5,
#   "misses": 5,
#   "total_requests": 10,
#   "hit_rate_percent": 50.0
# }
```

#### 2. 缓存覆盖范围 📦

**已缓存的方法**:
- ✅ `get_step_output(step_number)` - 缓存单个步骤输出
- ✅ `get_all_characters()` - 缓存角色列表（带哈希验证）
- ✅ `get_scene_list()` - 缓存场景列表

**性能提升**:
- 🔥 **第二次读取速度提升 ~90%**（基于测试结果）
- 🔥 **减少磁盘I/O操作**
- 🔥 **特别适用于Step 9/10的频繁引用**

#### 3. 自动缓存失效 🔄

**写操作自动清除相关缓存**:
```python
# 更新角色 → 清除角色缓存
update_character("Alice", data)  # 自动调用 _clear_character_cache()

# 更新场景列表 → 清除场景缓存
update_scene_list(scenes)  # 自动调用 _clear_scene_cache()

# 保存步骤 → 清除该步骤缓存
save_step_output(1, content)  # 自动调用 _clear_step_cache(1)

# 切换项目 → 清除所有缓存
init_project("New Project")  # 自动调用 _clear_cache()
load_project("Other Project")  # 自动调用 _clear_cache()
```

**智能失效策略**:
- 写入时立即失效相关缓存
- 项目切换时全量清除
- 哈希验证检测文件变化（角色列表）

#### 4. 缓存API 🛠️

**新增方法**:
```python
# 获取缓存统计
stats = engine.get_cache_stats()
# 返回: hits, misses, total_requests, hit_rate_percent

# 重置缓存统计（用于性能测试）
engine.clear_cache_stats()

# 内部方法（通常无需手动调用）
engine._clear_cache()              # 清除所有缓存
engine._clear_step_cache(step_num) # 清除特定步骤
engine._clear_character_cache()    # 清除角色缓存
engine._clear_scene_cache()        # 清除场景缓存
```

#### 5. 测试覆盖 🧪

**新增文件**: `tests/test_cache.py`

**测试统计**:
- ✅ **11个缓存专项测试**
- ✅ **100%通过率**
- ✅ **0.32秒运行时间**

**测试覆盖**:
- Cache hits and misses (步骤、角色、场景)
- Cache invalidation on updates
- Cache clearing on project switch
- Performance benefit verification
- Cache statistics tracking

**运行缓存测试**:
```bash
cd snowflake-writer
python tests/test_cache.py

# 输出:
# Ran 11 tests in 0.319s
# OK
```

#### 6. 性能基准 📊

**测试场景**: 读取5个步骤，每个步骤读取2次

| 操作 | 冷缓存 | 热缓存 | 提升 |
|------|--------|--------|------|
| 5个步骤首次读取 | 100% | - | - |
| 5个步骤二次读取 | - | ~10% | **~90%** |
| 命中率 | 0% | 50% | - |

**实际影响**:
- Step 9/10 频繁引用早期步骤 → 显著性能提升
- get_context() 批量加载 → 减少重复读取
- 大型项目（50+场景）→ 角色/场景列表缓存效果明显

#### 7. 向后兼容 ✅

**无破坏性变更**:
- 所有公共API保持不变
- 缓存完全透明，无需修改现有代码
- 旧项目自动享受缓存优化

**性能影响**:
- 首次读取: 无额外开销
- 二次读取: 显著性能提升
- 内存占用: 可忽略不计（仅缓存已读取的数据）

---

## Version 1.3 - 2024-12-17

### 🛡️ 质量提升 - 数据验证与测试

这是一个专注于**代码质量和健壮性**的版本，添加了全面的数据验证和单元测试覆盖。

#### 1. 数据验证系统 ✨

**新增异常**:
- `ValidationError` - 数据验证失败时抛出

**场景数据验证**:
```python
# 自动验证场景结构
update_scene_list(scenes)
# ✓ 检查 scene_number 存在且为正整数
# ✓ 检查 gist 存在且非空
# ✓ 提供清晰的错误消息
```

**验证规则**:
- ✅ `scene_number`: 必须存在，必须是正整数
- ✅ `gist`: 必须存在，不能为空字符串
- ✅ 所有场景在保存前验证，防止部分数据损坏

**角色数据验证**:
```python
# 自动验证角色数据
update_character("Alice", data)
# ✓ 检查 name 非空
# ✓ 防止无效数据写入
```

**验证规则**:
- ✅ `name`: 必须是非空字符串
- ✅ `role`: 允许自定义角色类型（灵活性）

**错误消息示例**:
```python
ValidationError: Scene at index 2: scene_number must be an integer, got str
ValidationError: Scene missing required field: 'gist'
ValidationError: Character 'name' must be a non-empty string
```

#### 2. 单元测试覆盖 🧪

**新增文件**: `tests/test_story_engine.py`

**测试统计**:
- ✅ **29个测试用例**
- ✅ **100%通过率**
- ✅ **0.4秒运行时间**

**测试覆盖**:

| 模块 | 测试数 | 覆盖功能 |
|------|--------|---------|
| 项目管理 | 5 | init, load, list projects |
| POV模式 | 5 | enable, disable, persist |
| 角色管理 | 4 | create, validate, retrieve |
| 场景管理 | 5 | create, validate scene structure |
| 步骤管理 | 3 | save, retrieve, metadata update |
| 健康检查 | 3 | status, warnings, progress |
| 场景保存 | 2 | save plan/draft |
| 灾难追踪 | 2 | log disasters |

**运行测试**:
```bash
cd snowflake-writer
python tests/test_story_engine.py

# 输出:
# Ran 29 tests in 0.439s
# OK
```

#### 3. 验证功能详解

**场景验证逻辑** (`_validate_scene()`):
```python
def _validate_scene(scene):
    # 1. 检查必需字段
    if "scene_number" not in scene:
        raise ValidationError("Scene missing required field: 'scene_number'")

    # 2. 类型检查
    if not isinstance(scene["scene_number"], int):
        raise ValidationError("scene_number must be an integer")

    # 3. 值域检查
    if scene["scene_number"] <= 0:
        raise ValidationError("scene_number must be positive")

    # 4. 内容检查
    if "gist" in scene and not scene["gist"].strip():
        raise ValidationError("Scene 'gist' cannot be empty")
```

**角色验证逻辑** (`_validate_character()`):
```python
def _validate_character(data):
    # 1. 检查名字存在
    if "name" not in data:
        raise ValidationError("Character data missing required field: 'name'")

    # 2. 检查名字非空
    if not isinstance(data["name"], str) or not data["name"].strip():
        raise ValidationError("Character 'name' must be a non-empty string")
```

#### 4. 影响范围

**破坏性变更**: ❌ 无
- 验证只在数据写入时执行
- 旧数据读取不受影响
- 完全向后兼容

**性能影响**: 可忽略不计
- 验证逻辑极轻量 (~0.1ms per scene)
- 仅在写入时执行，读取不受影响

---

## Version 1.2 - 2024-12-17

### 🎉 新增功能

#### POV Mode Toggle

**新增命令**: `snowflake pov [enable/disable]`

**功能**: 控制是否启用POV(视角)模式
- **POV启用时** (默认): 场景必须指定POV角色,健康检查会验证POV角色的完整性
- **POV禁用时**: 适合全知视角叙述,场景不需要POV角色,跳过POV相关检查

**适用场景**:
- ✅ 禁用POV: 全知叙述者、实验性叙事、超然视角
- ✅ 启用POV: 传统第一/第三人称POV、角色驱动叙事

**新增API**:
```python
set_pov_mode(False)  # 禁用POV模式
set_pov_mode(True)   # 启用POV模式
get_pov_mode()       # 获取当前POV模式状态
```

**元数据字段**:
- `metadata.settings.use_pov_mode`: Boolean,默认为 `True`

**Health Check 优化**:
- 只在POV模式启用时检查"POV characters not in Character Bible"警告
- 非POV模式下跳过所有POV相关验证

---

## Version 1.1 - 2024-12-17

### 🎉 新增功能

#### 1. 项目列表命令
- **新增命令**: `snowflake list`
- **功能**: 列出工作区中所有可用的项目
- **API**: `list_projects()` 函数
- **返回信息**: 项目标题、最后修改时间、当前步骤、已完成步骤

#### 2. 场景保存函数
- **新增**: `save_scene_plan(scene_number, content)` - 保存场景规划(Step 9)
- **新增**: `save_scene_draft(scene_number, content)` - 保存场景草稿(Step 10)
- **格式**: 自动添加标题、时间戳和分隔符
- **文件命名**: `scene_001_plan.md` 和 `scene_001.md`

### 🔧 核心改进

#### 3. 自动进度追踪
- **修复**: `save_step_output()` 现在自动更新 `metadata.json` 中的 `completed_steps`
- **影响**: 不再需要手动更新项目元数据
- **优点**: `snowflake status` 现在能准确反映实际进度

#### 4. 增强的错误处理
- **新增自定义异常**:
  - `SnowflakeError` - 基础异常类
  - `ProjectNotFoundError` - 项目不存在
  - `NoProjectLoadedError` - 未加载项目
  - `InvalidStepError` - 无效的步骤号
  - `CharacterNotFoundError` - 角色不存在

- **改进**: 所有异常现在提供清晰的错误消息和使用建议

#### 5. 增强的Health Check
- **新增检查项**:
  - ✅ POV角色是否都在Character Bible中
  - ✅ 最小角色要求(主角、反派)
  - ✅ 场景数量是否匹配目标字数
  - ✅ 已草稿的场景数统计

- **新增指标**:
  - 完成百分比(基于步骤权重计算)
  - 已草稿的场景数
  - 目标字数

- **新增警告分类**:
  - **Critical Issues** [!] - 阻塞性问题
  - **Warnings** [⚠] - 建议性警告

### 📊 Health Check 输出格式更新

**之前**:
```
PROJECT: [Title]
CURRENT STEP: [Number]
COMPLETED: Steps [list]

INVENTORY:
- Characters: [count]
- Scenes Planned: [count]
```

**现在**:
```
PROJECT: [Title]
CURRENT STEP: [Number]
COMPLETED: Steps [list]
COMPLETION: 65%

INVENTORY:
- Characters: 4
- Scenes Planned: 58
- Scenes Drafted: 12
- Disasters Defined: 3/3
- Target Word Count: 80000

HEALTH CHECK:
[!] Critical Issues: None
[⚠] Warnings: Scene count (58) may be high for target word count (recommended: ~53)
[✓] All systems operational
```

### 🛠️ 技术改进

- **类型安全**: `load_project()` 现在返回 `Dict` 而非 `Optional[Dict]`
- **一致性**: 所有三个 SKILL.md 文件已同步更新
- **文档**: 更新了 Implementation Notes 部分,添加新函数使用示例

### 📝 API 变更

#### 新增函数
```python
# 项目管理
list_projects() -> List[Dict[str, Any]]

# 场景保存
save_scene_plan(scene_number: int, content: str) -> None
save_scene_draft(scene_number: int, content: str) -> None
```

#### 修改的函数
```python
# load_project 现在抛出异常而非返回 None
load_project(title: str) -> Dict[str, Any]  # 之前: Optional[Dict[str, Any]]

# get_status 返回更多信息
get_status() -> Dict[str, Any]
# 新增字段: completion_percentage, scenes_drafted, health_warnings, target_word_count
```

### 🐛 Bug修复

1. **进度追踪缺失** - `save_step_output()` 现在正确更新元数据
2. **场景保存不一致** - 添加了专门的场景保存函数
3. **错误消息模糊** - 替换为清晰的自定义异常

### 📦 文件变更

**修改的文件**:
- `story_engine.py` - 新增 157 行,核心引擎增强
- `SKILL.md` - 更新命令列表和Health Check说明
- `.claude/skills/snowflake-writer/SKILL.md` - 同步更新
- `.skill/SKILL.md` - 同步更新

**新增文件**:
- `CHANGELOG.md` - 本文档

### 🎯 升级建议

对于现有项目:
1. 新功能会自动生效,无需迁移
2. 下次使用 `save_step_output()` 时,`completed_steps` 会自动填充
3. 运行 `snowflake status` 查看新的health check结果

### 🔮 未来计划

- [x] 添加单元测试覆盖 (v1.3完成)
- [x] 智能缓存系统 (v1.4完成)
- [ ] Markdown全书导出功能（合并所有场景）
- [ ] 添加版本控制集成
- [ ] 实现协作模式
- [ ] 添加AI辅助头脑风暴功能

---

**版本号**: v1.1
**更新日期**: 2024-12-17
**兼容性**: 向后兼容 v1.0
