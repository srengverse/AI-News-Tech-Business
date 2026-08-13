import ast
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "news.py"
DASHBOARD = ROOT / "dashboard.html"
SCHEMA = ROOT / "SUPABASE_SCHEMA.sql"


class ProjectSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_text = SOURCE.read_text(encoding="utf-8")
        cls.dashboard_text = DASHBOARD.read_text(encoding="utf-8")
        cls.schema_text = SCHEMA.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source_text)

    def test_python_source_compiles(self):
        compile(self.source_text, str(SOURCE), "exec")

    def test_required_runtime_functions_exist(self):
        functions = {
            node.name
            for node in ast.walk(self.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in {
            "check_environment",
            "is_safe_public_url",
            "fetch_feed",
            "fetch_article_image_url",
            "cleanup_cache",
            "worker",
        }:
            self.assertIn(name, functions)

    def test_all_news_categories_are_present(self):
        for category in ("finance", "technology", "business"):
            self.assertRegex(self.source_text, rf'"{category}"\s*:\s*\[')
        self.assertEqual(len(re.findall(r'\{"name":', self.source_text)), 16)

    def test_image_payload_validation_is_present(self):
        for marker in ("validate_image_bytes", "LOAD_TRUNCATED_IMAGES", "candidate.verify()", "decoded.load()", "MAX_IMAGE_BYTES"):
            self.assertIn(marker, self.source_text)
        self.assertIn("empty image payload", self.source_text)
        self.assertIn("invalid or truncated image", self.source_text)

    def test_reel_voiceover_pipeline_is_present(self):
        for name in ("build_khmer_narration", "generate_voiceover", "render", "post_facebook_reel", "post_telegram_video"):
            self.assertIn(name, self.source_text)
        self.assertIn("MEDIA_MODE", self.source_text)
        self.assertIn("GEMINI_TTS_MODEL", self.source_text)
        self.assertIn("GEMINI_API_KEYS", self.source_text)
        self.assertNotIn("OPENAI_API_KEY", self.source_text)
        self.assertIn("ffmpeg", self.source_text)
        self.assertIn("Speak in Khmer", self.source_text)

    def test_security_controls_are_present(self):
        self.assertIn("is_safe_public_url", self.source_text)
        self.assertIn("MAX_IMAGE_BYTES", self.source_text)
        self.assertIn("MAX_FEED_BYTES", self.source_text)
        self.assertIn("X-Dashboard-Token", self.source_text)
        self.assertIn("hmac.compare_digest", self.source_text)

    def test_dashboard_escapes_quotes_and_markup(self):
        self.assertIn("&quot;", self.dashboard_text)
        self.assertIn("&#39;", self.dashboard_text)
        self.assertNotIn("div.innerHTML", self.dashboard_text)

    def test_schema_has_backward_compatible_security_migration(self):
        self.assertIn("ADD COLUMN IF NOT EXISTS category", self.schema_text)
        self.assertIn("ADD COLUMN IF NOT EXISTS link", self.schema_text)
        self.assertIn("ENABLE ROW LEVEL SECURITY", self.schema_text)


if __name__ == "__main__":
    unittest.main()
