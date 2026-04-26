from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import run
from typing import Any
from urllib.parse import urlparse


@dataclass
class Session:
    id: str
    name: str
    created_at: float


@dataclass
class Skill:
    id: str
    name: str
    source_path: str
    imported_at: float


@dataclass
class Task:
    id: str
    title: str
    command: str
    status: str
    output: str
    error: str
    created_at: float


class AgentState:
    def __init__(self) -> None:
        self.sessions: list[Session] = [
            Session(id=self._id("sess"), name="Default Session", created_at=time.time())
        ]
        self.skills: list[Skill] = []
        self.tasks: list[Task] = []
        self.tool_logs: list[dict[str, Any]] = []
        self.operations: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def _id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def add_operation(self, step: str, command: str, output: str = "", error: str = "") -> None:
        with self._lock:
            self.operations.append(
                {
                    "id": self._id("op"),
                    "ts": time.time(),
                    "step": step,
                    "command": command,
                    "output": output,
                    "error": error,
                }
            )

    def add_tool_log(self, tool: str, action: str, detail: dict[str, Any]) -> None:
        with self._lock:
            self.tool_logs.append(
                {
                    "id": self._id("log"),
                    "ts": time.time(),
                    "tool": tool,
                    "action": action,
                    "detail": detail,
                }
            )

    def create_session(self, name: str) -> Session:
        sess = Session(id=self._id("sess"), name=name, created_at=time.time())
        with self._lock:
            self.sessions.append(sess)
        self.add_operation("create_session", f"session:create name={name}", output=sess.id)
        return sess

    def import_skill(self, source_path: str) -> Skill:
        p = Path(source_path)
        if not p.exists():
            raise FileNotFoundError(source_path)
        skill = Skill(id=self._id("skill"), name=p.stem, source_path=str(p), imported_at=time.time())
        with self._lock:
            self.skills.append(skill)
        self.add_tool_log("skill-manager", "import", {"path": str(p), "skill_id": skill.id})
        self.add_operation("import_skill", f"skill:import path={p}", output=skill.name)
        return skill

    def run_task(self, title: str, command: str) -> Task:
        task = Task(
            id=self._id("task"),
            title=title,
            command=command,
            status="running",
            output="",
            error="",
            created_at=time.time(),
        )
        with self._lock:
            self.tasks.append(task)

        self.add_operation("run_task", command)
        completed = run(command, shell=True, capture_output=True, text=True)
        task.status = "success" if completed.returncode == 0 else "failed"
        task.output = completed.stdout.strip()
        task.error = completed.stderr.strip()

        self.add_tool_log(
            "task-runner",
            "exec",
            {
                "task_id": task.id,
                "return_code": completed.returncode,
                "stdout": task.output,
                "stderr": task.error,
            },
        )
        self.add_operation(
            "task_result",
            command,
            output=task.output,
            error=task.error,
        )
        return task


STATE = AgentState()


class Handler(BaseHTTPRequestHandler):
    server_version = "GenericaLocalAPI/0.1"

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"ok": True})
            return
        if path == "/sessions":
            self._send(200, [asdict(s) for s in STATE.sessions])
            return
        if path == "/tasks":
            self._send(200, [asdict(t) for t in STATE.tasks])
            return
        if path == "/skills":
            self._send(200, [asdict(s) for s in STATE.skills])
            return
        if path == "/tool-logs":
            self._send(200, STATE.tool_logs)
            return
        if path == "/operations":
            self._send(200, STATE.operations)
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            data = self._read_json()
            if path == "/sessions":
                name = data.get("name", "New Session")
                self._send(201, asdict(STATE.create_session(name)))
                return
            if path == "/skills/import":
                source_path = data.get("source_path", "")
                self._send(201, asdict(STATE.import_skill(source_path)))
                return
            if path == "/tasks/run":
                title = data.get("title", "Task")
                command = data.get("command", "echo hello")
                self._send(201, asdict(STATE.run_task(title, command)))
                return
            self._send(404, {"error": "not found"})
        except FileNotFoundError as exc:
            self._send(400, {"error": f"file not found: {exc}"})
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        return


def start_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


if __name__ == "__main__":
    httpd = start_server()
    print(f"serving at http://{httpd.server_address[0]}:{httpd.server_address[1]}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        httpd.shutdown()
