# GenericaAgentForWin7

最小可运行版本：

- **Agent 核心**：本地 HTTP API（可替换 IPC 实现），维护会话、任务、工具日志、技能、操作流水。
- **GUI（Tkinter）**：会话区、任务列表、工具调用日志、技能管理页、操作流水面板。
- **Win7 兼容测试清单**：中文输入、字体、DPI、窗口缩放、文件拖拽。

## 运行

```bash
python3 app.py
```

启动后会同时拉起本地 API（默认 `127.0.0.1:8765`）和 GUI。

## 闭环验收流程（Win7）

1. 在“技能管理”页点击“导入技能”（或输入路径后导入）
2. 在“任务列表”页创建任务并运行（可执行命令）
3. 在“工具调用日志”和“操作流水”面板查看每步命令/输出/错误

## 架构说明

- `core/local_api.py`: Agent 核心 + 本地 API 服务。
- `gui/app.py`: GUI 客户端，仅通过 HTTP 与核心通信，实现前后端解耦。
- `app.py`: 启动入口（先启动核心，再启动 GUI）。
- `tests/test_core_api.py`: API 基础测试与闭环验证。
- `docs/win7_compat_checklist.md`: Win7 UI 兼容测试项与记录模板。
