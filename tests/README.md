# Snowflake Writer - 测试套件

## 测试统计

- **测试用例总数**: 53 (29 核心 + 11 缓存 + 13 RAG)
- **测试通过率**: 100%
- **平均运行时间**: ~1.0秒（不含RAG模型下载）

## 运行测试

### 方法1: 直接运行
```bash
cd snowflake-writer
python tests/test_story_engine.py
```

### 方法2: 运行缓存测试
```bash
cd snowflake-writer
python tests/test_cache.py
```

### 方法3: 运行RAG测试
```bash
cd snowflake-writer
python tests/test_style_rag.py
```

**注意**: RAG测试需要安装依赖
```bash
pip install chromadb sentence-transformers
```

如果依赖未安装，测试会自动跳过。

### 方法4: 使用 pytest (推荐)
```bash
cd snowflake-writer
pip install pytest  # 如果未安装
pytest tests/ -v
```

### 方法4: 运行特定测试类
```bash
# 只测试项目管理
python -m unittest tests.test_story_engine.TestProjectManagement

# 只测试数据验证
python -m unittest tests.test_story_engine.TestSceneManagement
```

## 测试覆盖范围

### 项目管理 (5 tests)
- ✅ 项目初始化创建正确的目录结构
- ✅ 加载已存在的项目
- ✅ 加载不存在的项目抛出异常
- ✅ 列出空项目列表
- ✅ 列出多个项目

### POV模式 (5 tests)
- ✅ 默认启用POV模式
- ✅ 禁用POV模式
- ✅ 重新启用POV模式
- ✅ POV模式在重新加载后持久化
- ✅ 无项目时设置POV模式抛出异常

### 角色管理 (4 tests)
- ✅ 创建基础角色
- ✅ 空名字验证失败
- ✅ 缺失名字验证失败
- ✅ 获取所有角色

### 场景管理 (5 tests)
- ✅ 使用有效数据更新场景列表
- ✅ 缺少scene_number验证失败
- ✅ scene_number类型错误验证失败
- ✅ 负数scene_number验证失败
- ✅ 空gist验证失败

### 步骤管理 (3 tests)
- ✅ save_step_output更新metadata
- ✅ save_step_output创建文件
- ✅ 获取步骤输出

### 健康检查 (3 tests)
- ✅ 基本状态检索
- ✅ 有进度的状态检索
- ✅ 健康警告生成

### 场景保存 (2 tests)
- ✅ 保存场景计划
- ✅ 保存场景草稿

### 灾难追踪 (2 tests)
- ✅ 记录单个灾难
- ✅ 记录多个灾难

### 缓存系统 (11 tests) 🚀
- ✅ 缓存统计初始状态为零
- ✅ 步骤输出缓存未命中
- ✅ 步骤输出缓存命中
- ✅ 角色缓存未命中后命中
- ✅ 场景列表缓存未命中后命中
- ✅ 角色更新时缓存失效
- ✅ 场景更新时缓存失效
- ✅ 步骤保存时缓存失效
- ✅ 项目切换时清除缓存
- ✅ 缓存性能提升验证
- ✅ 清除缓存统计

### RAG风格系统 (13 tests) 🎨
- ✅ RAG系统初始化
- ✅ 添加参考小说
- ✅ 文本智能分块
- ✅ 块类型自动分类（对话/动作/叙述）
- ✅ 检索风格样本
- ✅ 获取风格上下文
- ✅ 列出所有参考
- ✅ 删除指定参考
- ✅ 清除所有参考
- ✅ 统计信息获取
- ✅ 重复参考错误处理
- ✅ 依赖检查功能
- ✅ 场景类型匹配检索

## 测试输出示例

```
test_get_all_characters ... ok
test_update_character_basic ... ok
test_update_character_validation_empty_name ... ok
test_update_character_validation_missing_name ... ok
test_log_disaster ... ok
test_log_multiple_disasters ... ok
test_get_status_basic ... ok
test_get_status_health_warnings ... ok
test_get_status_with_progress ... ok
test_pov_mode_default_enabled ... ok
test_pov_mode_persists_after_reload ... ok
test_pov_mode_without_project_raises_error ... ok
test_set_pov_mode_disable ... ok
test_set_pov_mode_enable ... ok
test_init_project_creates_structure ... ok
test_list_projects_empty ... ok
test_list_projects_multiple ... ok
test_load_project_not_found ... ok
test_load_project_success ... ok
test_update_scene_list_valid ... ok
test_update_scene_list_validation_empty_gist ... ok
test_update_scene_list_validation_invalid_scene_number_type ... ok
test_update_scene_list_validation_missing_scene_number ... ok
test_update_scene_list_validation_negative_scene_number ... ok
test_save_scene_draft ... ok
test_save_scene_plan ... ok
test_get_step_output ... ok
test_save_step_output_creates_file ... ok
test_save_step_output_updates_metadata ... ok

----------------------------------------------------------------------
Ran 29 tests in 0.439s

OK
```

**缓存测试输出示例**:
```
test_cache_cleared_on_project_switch ... ok
test_cache_invalidation_on_character_update ... ok
test_cache_invalidation_on_scene_update ... ok
test_cache_invalidation_on_step_save ... ok
test_cache_performance_benefit ... ok
test_cache_stats_initial ... ok
test_character_cache_miss_then_hit ... ok
test_clear_cache_stats ... ok
test_scene_list_cache_miss_then_hit ... ok
test_step_output_cache_hit ... ok
test_step_output_cache_miss ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.319s

OK
```

## 添加新测试

在 `test_story_engine.py` 中添加新的测试类或方法：

```python
class TestNewFeature(TestSnowflakeEngine):
    """Tests for new feature"""

    def test_new_functionality(self):
        """Test new functionality"""
        self.engine.init_project("Test")
        # ... your test code ...
        self.assertEqual(expected, actual)
```

## 持续集成

建议在提交代码前运行所有测试：

```bash
# 运行测试
python tests/test_story_engine.py

# 如果所有测试通过，再提交
git add .
git commit -m "Your commit message"
```

## 故障排除

### 测试失败: "No module named 'story_engine'"
**解决方案**: 确保从 `snowflake-writer` 目录运行测试

### 测试失败: 权限错误
**解决方案**: 确保有临时目录的写权限

### 测试失败: 文件已存在
**解决方案**: 测试使用临时目录，会自动清理。如果失败，手动删除测试临时文件
