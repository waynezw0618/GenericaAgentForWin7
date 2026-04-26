# Skill Package & Import/Management CLI

本仓库实现了技能包规范、`import_skill` 导入流程、导入校验、以及技能管理接口（CLI 先行）。

## 1) 技能包规范（`skill.yaml`）

每个技能包目录（或 zip）必须包含 `skill.yaml`：

```yaml
name: autoclaw_hello
version: 1.0.0
entry: main.py
dependencies: []
permissions:
  - proc.exec
```

字段说明：

- `name`: 技能名，2-64 字符，字母开头，支持 `-`/`_`。
- `version`: SemVer（如 `1.0.0`）。
- `entry`: 入口脚本相对路径。
- `dependencies`: 依赖列表（字符串数组）。
- `permissions`: 权限列表（字符串数组），允许值：
  - `fs.read`
  - `fs.write`
  - `net.http`
  - `proc.exec`
  - `ui.notify`

## 2) `import_skill` 流程

支持两种输入：

1. 技能目录（autoclaw 产物目录）
2. 技能 zip（autoclaw 打包产物）

导入行为：

- 读取并校验 `skill.yaml`
- 校验入口文件是否存在
- 安装到 `.skills/installed/<name>/<version>`
- 更新 `.skills/registry.json`
- 任一步失败时执行回滚（删除已复制目录，不写入/恢复 registry）

## 3) 导入校验

- 缺文件：缺 `skill.yaml` / 缺入口文件会报错。
- 版本冲突：同名同版本重复导入会报错。
- 非法路径：
  - `entry` 不能逃逸技能目录（禁止 `../`）
  - zip 不能含绝对路径或 `..` 逃逸条目
- 权限越界：`permissions` 中含未授权 scope 会报错。

## 4) 管理接口（CLI）

```bash
python3 cli.py import-skill <path_or_zip>
python3 cli.py enable <skill_name>
python3 cli.py disable <skill_name>
python3 cli.py uninstall <skill_name>
python3 cli.py rollback <skill_name>
python3 cli.py run <skill_name>
python3 cli.py list
```

## 验收示例

仓库提供 2+ autoclaw 示例技能：

- `skills/autoclaw/hello_v1`
- `skills/autoclaw/hello_v2`（用于回滚验证）
- `skills/autoclaw/time_echo`

示例流程：

```bash
python3 cli.py import-skill skills/autoclaw/hello_v1
python3 cli.py import-skill skills/autoclaw/hello_v2
python3 cli.py import-skill skills/autoclaw/time_echo

python3 cli.py enable autoclaw_hello
python3 cli.py run autoclaw_hello

python3 cli.py rollback autoclaw_hello
python3 cli.py run autoclaw_hello

python3 cli.py enable autoclaw_time
python3 cli.py run autoclaw_time
```
