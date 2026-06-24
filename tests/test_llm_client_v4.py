import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autosolver_llm_v4 import llm_client_v4


class TestClient(unittest.TestCase):
    def test_fake_queue(self):
        c = llm_client_v4.FakeModelClient(["a", "b"])
        self.assertEqual(c.complete([]), "a")
        self.assertEqual(c.complete([]), "b")
        with self.assertRaises(llm_client_v4.LLMError):
            c.complete([])

    def test_make_client_fake(self):
        c = llm_client_v4.make_client("fake", scripted_outputs=["x"])
        self.assertEqual(c.complete([]), "x")

    def test_deepseek_config(self):
        # 不联网；只验证配置正确
        c = llm_client_v4.LLMClient(provider="deepseek", api_key="dummy")
        self.assertEqual(c.model, "deepseek-chat")
        self.assertEqual(c.reason_model, "deepseek-reasoner")
        self.assertTrue(c.url.endswith("/chat/completions"))
        self.assertTrue(c.has_key)

    def test_unknown_provider(self):
        with self.assertRaises(llm_client_v4.LLMError):
            llm_client_v4.LLMClient(provider="nope")


if __name__ == "__main__":
    unittest.main()
