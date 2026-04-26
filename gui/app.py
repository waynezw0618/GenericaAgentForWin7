from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.error import URLError
from urllib.request import Request, urlopen


class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8765") -> None:
        self.base_url = base_url.rstrip("/")

    def get(self, path: str):
        with urlopen(f"{self.base_url}{path}", timeout=4) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def post(self, path: str, payload: dict):
        req = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))


class GenericaGUI(tk.Tk):
    def __init__(self, client: ApiClient) -> None:
        super().__init__()
        self.client = client
        self.title("Generica Agent for Win7")
        self.geometry("1100x760")
        self.minsize(900, 620)

        default_font = ("Microsoft YaHei UI", 10)
        self.option_add("*Font", default_font)

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)

        self.session_tab = ttk.Frame(tabs)
        self.task_tab = ttk.Frame(tabs)
        self.log_tab = ttk.Frame(tabs)
        self.skill_tab = ttk.Frame(tabs)
        self.pipeline_tab = ttk.Frame(tabs)

        tabs.add(self.session_tab, text="会话区")
        tabs.add(self.task_tab, text="任务列表")
        tabs.add(self.log_tab, text="工具调用日志")
        tabs.add(self.skill_tab, text="技能管理")
        tabs.add(self.pipeline_tab, text="操作流水")

        self._build_sessions()
        self._build_tasks()
        self._build_logs()
        self._build_skills()
        self._build_pipeline()

        refresh_btn = ttk.Button(self, text="刷新全部", command=self.refresh_all)
        refresh_btn.pack(side="bottom", pady=6)

        self.refresh_all()

    def _safe(self, fn):
        try:
            fn()
        except URLError:
            messagebox.showerror("连接失败", "无法连接本地 Agent API，请确认 core 已启动。")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("错误", str(exc))

    def _build_sessions(self):
        top = ttk.Frame(self.session_tab)
        top.pack(fill="x", padx=8, pady=8)
        self.session_name = tk.StringVar(value="新会话")
        ttk.Entry(top, textvariable=self.session_name, width=40).pack(side="left")
        ttk.Button(top, text="创建会话", command=lambda: self._safe(self.create_session)).pack(side="left", padx=6)

        self.session_list = tk.Listbox(self.session_tab)
        self.session_list.pack(fill="both", expand=True, padx=8, pady=8)

    def _build_tasks(self):
        form = ttk.Frame(self.task_tab)
        form.pack(fill="x", padx=8, pady=8)

        self.task_title = tk.StringVar(value="示例任务")
        self.task_cmd = tk.StringVar(value="echo hello-win7")

        ttk.Label(form, text="标题").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.task_title, width=24).grid(row=0, column=1, padx=4)
        ttk.Label(form, text="命令").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.task_cmd, width=56).grid(row=0, column=3, padx=4)
        ttk.Button(form, text="运行任务", command=lambda: self._safe(self.run_task)).grid(row=0, column=4, padx=4)

        self.task_tree = ttk.Treeview(self.task_tab, columns=("title", "status", "cmd"), show="headings")
        for col, text, w in [("title", "标题", 180), ("status", "状态", 90), ("cmd", "命令", 680)]:
            self.task_tree.heading(col, text=text)
            self.task_tree.column(col, width=w, anchor="w")
        self.task_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _build_logs(self):
        self.log_text = tk.Text(self.log_tab, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    def _build_skills(self):
        panel = ttk.Frame(self.skill_tab)
        panel.pack(fill="x", padx=8, pady=8)

        self.skill_path = tk.StringVar()
        ttk.Entry(panel, textvariable=self.skill_path, width=72).pack(side="left")
        ttk.Button(panel, text="浏览", command=self.pick_skill).pack(side="left", padx=4)
        ttk.Button(panel, text="导入技能", command=lambda: self._safe(self.import_skill)).pack(side="left")

        tip = "支持拖拽文件到输入框（Win7 上建议先启用系统拖拽兼容层）"
        ttk.Label(self.skill_tab, text=tip).pack(anchor="w", padx=8)

        self.skill_list = tk.Listbox(self.skill_tab)
        self.skill_list.pack(fill="both", expand=True, padx=8, pady=8)

    def _build_pipeline(self):
        cols = ("step", "command", "output", "error")
        self.pipeline_tree = ttk.Treeview(self.pipeline_tab, columns=cols, show="headings")
        widths = {"step": 120, "command": 320, "output": 300, "error": 320}
        titles = {"step": "步骤", "command": "命令", "output": "输出", "error": "错误"}
        for c in cols:
            self.pipeline_tree.heading(c, text=titles[c])
            self.pipeline_tree.column(c, width=widths[c], anchor="w")
        self.pipeline_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_all(self):
        self._safe(self.load_sessions)
        self._safe(self.load_tasks)
        self._safe(self.load_logs)
        self._safe(self.load_skills)
        self._safe(self.load_pipeline)

    def create_session(self):
        self.client.post("/sessions", {"name": self.session_name.get().strip() or "新会话"})
        self.load_sessions()

    def run_task(self):
        self.client.post(
            "/tasks/run",
            {
                "title": self.task_title.get().strip() or "任务",
                "command": self.task_cmd.get().strip() or "echo default",
            },
        )
        self.refresh_all()

    def import_skill(self):
        path = self.skill_path.get().strip()
        if not path:
            messagebox.showwarning("提示", "请先选择技能文件")
            return
        self.client.post("/skills/import", {"source_path": path})
        self.refresh_all()

    def pick_skill(self):
        path = filedialog.askopenfilename(title="选择技能文件")
        if path:
            self.skill_path.set(path)

    def load_sessions(self):
        sessions = self.client.get("/sessions")
        self.session_list.delete(0, "end")
        for s in sessions:
            self.session_list.insert("end", f"{s['id']} | {s['name']}")

    def load_tasks(self):
        for row in self.task_tree.get_children():
            self.task_tree.delete(row)
        for t in self.client.get("/tasks"):
            self.task_tree.insert("", "end", values=(t["title"], t["status"], t["command"]))

    def load_logs(self):
        self.log_text.delete("1.0", "end")
        logs = self.client.get("/tool-logs")
        for log in logs[-200:]:
            line = f"[{log['tool']}/{log['action']}] {json.dumps(log['detail'], ensure_ascii=False)}\n"
            self.log_text.insert("end", line)

    def load_skills(self):
        self.skill_list.delete(0, "end")
        for s in self.client.get("/skills"):
            self.skill_list.insert("end", f"{s['name']} <- {s['source_path']}")

    def load_pipeline(self):
        for row in self.pipeline_tree.get_children():
            self.pipeline_tree.delete(row)
        for op in self.client.get("/operations")[-300:]:
            self.pipeline_tree.insert(
                "",
                "end",
                values=(op["step"], op["command"], op.get("output", ""), op.get("error", "")),
            )


def run_gui(base_url: str = "http://127.0.0.1:8765"):
    app = GenericaGUI(ApiClient(base_url))
    app.mainloop()


if __name__ == "__main__":
    run_gui()
