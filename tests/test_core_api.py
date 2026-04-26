from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from core.local_api import start_server


class TestCoreAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_server("127.0.0.1", 8877)
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path: str):
        with urlopen(f"http://127.0.0.1:8877{path}", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def post(self, path: str, payload: dict):
        req = Request(
            f"http://127.0.0.1:8877{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_acceptance_loop(self):
        with tempfile.TemporaryDirectory() as td:
            skill_file = Path(td) / "example_skill.yaml"
            skill_file.write_text("name: demo", encoding="utf-8")

            imported = self.post("/skills/import", {"source_path": str(skill_file)})
            self.assertIn("skill_", imported["id"])

            task = self.post("/tasks/run", {"title": "run", "command": "echo done"})
            self.assertEqual("success", task["status"])

            logs = self.get("/tool-logs")
            ops = self.get("/operations")
            self.assertTrue(any(l["tool"] == "skill-manager" for l in logs))
            self.assertTrue(any(o["step"] == "task_result" for o in ops))


if __name__ == "__main__":
    unittest.main()
