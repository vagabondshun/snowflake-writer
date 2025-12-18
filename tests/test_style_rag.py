"""
测试RAG风格系统

注意：这些测试需要安装 chromadb 和 sentence-transformers
如果依赖未安装，测试会自动跳过
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from style_rag import StyleRAG, check_dependencies, DependencyError
    DEPENDENCIES_AVAILABLE = check_dependencies()["all_available"]
except ImportError:
    DEPENDENCIES_AVAILABLE = False


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "RAG dependencies not installed")
class TestStyleRAG(unittest.TestCase):
    """测试RAG风格系统"""

    def setUp(self):
        """为每个测试创建临时项目目录"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.rag = StyleRAG(self.temp_dir)

        # 测试用参考文本
        self.sample_novel = """
        多年以后，面对行刑队，奥雷里亚诺·布恩迪亚上校将会回想起，
        他父亲带他去见识冰块的那个遥远的下午。那时的马孔多是一个
        二十户人家的村落，土屋就盖在河岸上，河水清澈，沿着遍布石头
        的河床流去，河里的石头光滑、雪白，活像史前的巨蛋。

        "你疯了吗？"他的妻子问。

        "没有，"他平静地回答，"我只是在思考时间的问题。"

        他走到窗前，看着外面的雨。雨下得很大，打在屋顶上发出
        沉闷的声响。他想起了童年时期的那个下午，父亲第一次带他
        看到冰块时的情景。

        那是一个炎热的下午。父亲牵着他的手，走进帐篷。帐篷里
        很暗，只有一道光从顶部照下来，照在那块巨大的冰块上。
        """

    def tearDown(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """测试RAG系统初始化"""
        self.assertIsNotNone(self.rag)
        self.assertTrue(self.rag.style_ref_path.exists())
        self.assertEqual(len(self.rag.metadata["references"]), 0)

    def test_add_reference_novel(self):
        """测试添加参考小说"""
        result = self.rag.add_reference_novel(
            title="测试小说",
            content=self.sample_novel,
            author="测试作者",
            chunk_size=200,
            max_chunks=10
        )

        self.assertIn("ref_id", result)
        self.assertEqual(result["title"], "测试小说")
        self.assertGreater(result["chunks_added"], 0)
        self.assertGreater(result["total_chars"], 0)

    def test_text_chunking(self):
        """测试文本分块功能"""
        chunks = self.rag._chunk_text(self.sample_novel, chunk_size=200)

        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertIn("text", chunk)
            self.assertIn("char_count", chunk)
            self.assertLessEqual(chunk["char_count"], 300)  # 允许1.5x超出

    def test_chunk_type_classification(self):
        """测试块类型分类"""
        dialogue = '"你好吗？"他问道。"我很好。"她回答。'
        chunk_type = self.rag._classify_chunk_type(dialogue)
        self.assertEqual(chunk_type, "dialogue")

        # 需要超过300字符才会被分类为 description
        narrative = "那是一个漫长的夏天。阳光透过树叶洒在地上，形成斑驳的光影。" * 15
        chunk_type = self.rag._classify_chunk_type(narrative)
        self.assertEqual(chunk_type, "description")

    def test_retrieve_style_samples(self):
        """测试检索风格样本"""
        # 先添加参考
        self.rag.add_reference_novel(
            title="测试小说",
            content=self.sample_novel,
            chunk_size=150
        )

        # 检索相似样本
        samples = self.rag.retrieve_style_samples(
            query="他回想起童年的记忆",
            n_results=2
        )

        self.assertGreater(len(samples), 0)
        self.assertLessEqual(len(samples), 2)

        for sample in samples:
            self.assertIn("text", sample)
            self.assertIn("metadata", sample)
            self.assertIn("distance", sample)

    def test_get_style_context(self):
        """测试获取风格上下文"""
        self.rag.add_reference_novel(
            title="测试小说",
            content=self.sample_novel
        )

        context = self.rag.get_style_context(
            scene_description="主角回忆往事",
            scene_type="narrative",
            n_samples=3
        )

        self.assertIn("samples", context)
        self.assertIn("sample_count", context)
        self.assertIn("references", context)
        self.assertGreater(context["sample_count"], 0)

    def test_list_references(self):
        """测试列出所有参考"""
        self.rag.add_reference_novel("参考1", self.sample_novel)
        self.rag.add_reference_novel("参考2", self.sample_novel)

        refs = self.rag.list_references()
        self.assertEqual(len(refs), 2)

    def test_remove_reference(self):
        """测试删除参考"""
        result = self.rag.add_reference_novel("测试小说", self.sample_novel)
        ref_id = result["ref_id"]

        # 确认存在
        refs = self.rag.list_references()
        self.assertEqual(len(refs), 1)

        # 删除
        success = self.rag.remove_reference(ref_id)
        self.assertTrue(success)

        # 确认已删除
        refs = self.rag.list_references()
        self.assertEqual(len(refs), 0)

    def test_clear_all_references(self):
        """测试清除所有参考"""
        self.rag.add_reference_novel("参考1", self.sample_novel)
        self.rag.add_reference_novel("参考2", self.sample_novel)

        self.rag.clear_all_references()

        refs = self.rag.list_references()
        self.assertEqual(len(refs), 0)

    def test_statistics(self):
        """测试统计信息"""
        result = self.rag.add_reference_novel("测试小说", self.sample_novel)

        stats = self.rag.get_statistics()

        self.assertEqual(stats["reference_count"], 1)
        self.assertEqual(stats["total_chunks"], result["chunks_added"])
        self.assertGreater(stats["total_characters"], 0)
        self.assertEqual(stats["collection_count"], result["chunks_added"])

    def test_duplicate_reference_error(self):
        """测试重复添加参考会抛出错误"""
        self.rag.add_reference_novel("测试小说", self.sample_novel)

        with self.assertRaises(Exception):  # StyleRAGError
            self.rag.add_reference_novel("测试小说", self.sample_novel)


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "RAG dependencies not installed")
class TestFileParser(unittest.TestCase):
    """测试文件解析功能"""

    def setUp(self):
        """创建临时测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.rag = StyleRAG(self.temp_dir)

        # 创建测试TXT文件
        self.txt_file = self.temp_dir / "test_novel.txt"
        self.txt_content = """
        这是一个测试小说的开头。

        第一章

        多年以后，面对行刑队，奥雷里亚诺·布恩迪亚上校将会回想起，
        他父亲带他去见识冰块的那个遥远的下午。

        "你准备好了吗？"他问道。

        "我准备好了。"她回答。
        """
        with open(self.txt_file, 'w', encoding='utf-8') as f:
            f.write(self.txt_content)

    def tearDown(self):
        """清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_txt_file(self):
        """测试TXT文件解析"""
        result = self.rag.parse_file(self.txt_file)

        self.assertIn("content", result)
        self.assertIn("title", result)
        self.assertIn("format", result)
        self.assertEqual(result["format"], "txt")
        self.assertEqual(result["title"], "test_novel")
        self.assertGreater(result["char_count"], 0)

    def test_add_reference_from_txt_file(self):
        """测试从TXT文件添加参考"""
        result = self.rag.add_reference_from_file(
            self.txt_file,
            author="测试作者"
        )

        self.assertIn("ref_id", result)
        self.assertIn("source_file", result)
        self.assertEqual(result["source_format"], "txt")
        self.assertGreater(result["chunks_added"], 0)

    def test_scan_folder(self):
        """测试文件夹扫描"""
        # 创建多个测试文件
        for i in range(3):
            file_path = self.temp_dir / f"novel_{i}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"这是第{i}本测试小说的内容。" * 50)

        result = self.rag.scan_folder(self.temp_dir)

        # 至少应该有4个文件（包括setUp创建的）
        self.assertGreaterEqual(result["total_files"], 4)
        self.assertGreaterEqual(result["success_count"], 3)
        self.assertIn("success", result)
        self.assertIn("failed", result)

    def test_parse_unsupported_format(self):
        """测试不支持的文件格式"""
        unsupported_file = self.temp_dir / "test.doc"
        unsupported_file.touch()

        with self.assertRaises(Exception):
            self.rag.parse_file(unsupported_file)

    def test_parse_nonexistent_file(self):
        """测试不存在的文件"""
        with self.assertRaises(Exception):
            self.rag.parse_file(self.temp_dir / "nonexistent.txt")

    def test_txt_encoding_detection(self):
        """测试TXT编码自动检测"""
        # 创建GBK编码文件
        gbk_file = self.temp_dir / "gbk_novel.txt"
        gbk_content = "这是GBK编码的中文内容。"
        with open(gbk_file, 'w', encoding='gbk') as f:
            f.write(gbk_content)

        result = self.rag.parse_file(gbk_file)
        self.assertIn("这是GBK编码的中文内容", result["content"])


class TestDependencyCheck(unittest.TestCase):
    """测试依赖检查功能"""

    def test_check_dependencies(self):
        """测试依赖检查函数"""
        deps = check_dependencies()

        self.assertIn("chromadb", deps)
        self.assertIn("sentence_transformers", deps)
        self.assertIn("all_available", deps)
        self.assertIsInstance(deps["all_available"], bool)

    def test_check_file_parser_dependencies(self):
        """测试文件解析依赖检查"""
        try:
            from style_rag import check_file_parser_dependencies
            deps = check_file_parser_dependencies()

            self.assertIn("txt", deps)
            self.assertIn("pdf", deps)
            self.assertIn("epub", deps)
            self.assertTrue(deps["txt"])  # TXT应该总是可用
        except ImportError:
            self.skipTest("check_file_parser_dependencies not available")


if __name__ == '__main__':
    if not DEPENDENCIES_AVAILABLE:
        print("\n" + "="*70)
        print("警告: RAG依赖未安装，测试将被跳过")
        print("="*70)
        print("\n安装依赖: pip install chromadb sentence-transformers\n")

    unittest.main(verbosity=2)
