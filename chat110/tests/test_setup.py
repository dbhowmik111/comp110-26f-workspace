"""Confirm the provided runtime is installed without running unfinished code."""

import unittest
from pathlib import Path

from chat110.cli import select_next_token
from chat110.model import BUNDLE_CONFIG, BUNDLE_FILES, ROOT, load_config
from chat110.runtime import GemmaChat
from chat110.support import rank_indices


class SetupTests(unittest.TestCase):
    def test_runtime_and_student_modules_import(self):
        self.assertTrue(callable(GemmaChat))
        for stage in range(1, 5):
            with self.subTest(stage=stage):
                choose = select_next_token(stage, 0.9)
                self.assertTrue(callable(choose))
                self.assertTrue(choose.__module__.startswith("decoders."))
        self.assertEqual(rank_indices([0.125, 0.5, 0.125, 0.25]), [1, 3, 0, 2])

    def test_model_configuration_belongs_to_this_project(self):
        self.assertEqual(ROOT, Path(__file__).resolve().parents[1])
        self.assertTrue(BUNDLE_CONFIG.is_file())
        self.assertEqual(set(load_config()["files"]), set(BUNDLE_FILES))
        for relative in ("MODEL_USE.md", "NOTICE", "licenses/GEMMA_TERMS_OF_USE.md",
                         "licenses/GEMMA_PROHIBITED_USE_POLICY.md"):
            self.assertTrue((ROOT / relative).is_file())


if __name__ == "__main__":
    unittest.main()
