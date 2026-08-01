"""Tests against the deep execute interface (execute.py).

Stdlib unittest only so CI/hosts do not need pytest.
"""

from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import execute as core  # noqa: E402


class ExecuteApiTests(unittest.TestCase):
    def test_known_languages_nonempty(self):
        langs = core.known_languages()
        self.assertIn("python", langs)
        self.assertIn("ai", langs)
        self.assertIn("c", langs)

    def test_stats_single_and_multi(self):
        self.assertEqual(core._stats([])["samples"], 0)
        one = core._stats([10.0])
        self.assertEqual(one["avgMs"], 10.0)
        self.assertEqual(one["stdevMs"], 0.0)
        multi = core._stats([10.0, 20.0, 30.0])
        self.assertEqual(multi["samples"], 3)
        self.assertEqual(multi["avgMs"], 20.0)
        self.assertEqual(multi["minMs"], 10.0)
        self.assertEqual(multi["maxMs"], 30.0)
        self.assertIsNotNone(multi["stdevMs"])
        self.assertGreater(multi["stdevMs"], 0)

    def test_unknown_language(self):
        with self.assertRaises(core.UnknownLanguage):
            core.run_samples("not-a-language", samples=1)

    def test_run_samples_ai_requires_key_or_runs(self):
        import os
        if not os.environ.get("OPENAI_API_KEY"):
            # Without a key the live path should fail cleanly (config error).
            result = core.run_samples("ai", samples=1)
            self.assertEqual(result["samples"], 1)
            self.assertIn(result["exitCode"], (0, 1))
            if result["exitCode"] != 0:
                self.assertIn("OPENAI", result.get("stderr") or result.get("displayStdout") or "")
            return
        result = core.run_samples("ai", samples=1)
        self.assertEqual(result["exitCode"], 0)
        self.assertTrue(result.get("displayStdout"))
        self.assertIsNotNone(result.get("costUsd"))

    def test_run_samples_python(self):
        if not shutil.which("python3"):
            self.skipTest("python3 missing")
        result = core.run_samples("python", samples=3)
        self.assertEqual(result["exitCode"], 0)
        self.assertIn("Hello, World!", result.get("displayStdout") or result.get("stdout") or "")
        self.assertEqual(result["samples"], 3)
        self.assertIsNotNone(result["avgMs"])
        self.assertLessEqual(result["minMs"], result["avgMs"])
        self.assertLessEqual(result["avgMs"], result["maxMs"])

    def test_run_samples_bash(self):
        if not shutil.which("bash"):
            self.skipTest("bash missing")
        result = core.run_samples("bash", samples=2)
        self.assertEqual(result["exitCode"], 0)
        self.assertIn("Hello, World!", result.get("displayStdout", ""))

    def test_catalog_levels_shape(self):
        levels = core.catalog_levels()
        self.assertEqual(len(levels), len(core.BANDS))
        self.assertEqual(levels[0]["id"], "binary")
        for band in levels:
            self.assertIn("variants", band)
            self.assertTrue(band["variants"])
            for v in band["variants"]:
                self.assertIn("githubUrl", v)
                self.assertTrue(v["githubUrl"].startswith("https://github.com/"))

    def test_catalog_languages_matches_known(self):
        langs = core.catalog_languages()
        self.assertEqual({x["id"] for x in langs}, set(core.known_languages()))

    def test_benchmark_subset(self):
        if not shutil.which("python3"):
            self.skipTest("python3 missing")
        result = core.benchmark(samples=2, languages=["python", "bash"])
        self.assertEqual(result["samples"], 2)
        self.assertEqual(result["count"], 2)
        self.assertIn("hardware", result)
        ids = {r["id"] for r in result["rows"]}
        self.assertEqual(ids, {"python", "bash"})
        for row in result["rows"]:
            self.assertTrue(row["ok"], row)
            self.assertIsNotNone(row["avgMs"])
            self.assertIn("Hello, World!", row["stdout"])

    def test_hardware_info_keys(self):
        hw = core.hardware_info()
        self.assertIn("architecture", hw)
        self.assertIn("cpus", hw)
        self.assertIn("python", hw)


if __name__ == "__main__":
    unittest.main()
