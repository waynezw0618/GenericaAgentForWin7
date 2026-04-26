# Win7 安装与便携部署指南（GenericaAgent）

> 目标：在 **Windows 7 SP1 x64** 新机器上，15 分钟内完成安装并跑通示例任务。

## 1. 前置条件

- 操作系统：Windows 7 SP1（建议 64 位）。
- 必需运行库：
  - Microsoft Visual C++ 2015-2022 x86/x64 Redistributable。
  - .NET Framework 4.7.2（若程序依赖）。
- 推荐工具：
  - 7-Zip（用于解压便携包）。
  - PowerShell 5.1。

## 2. 产物说明

发布目录 `dist/win7/` 应至少包含：

- `GenericaAgent-<version>-win7-portable.zip`（**必须提供**）
- `GenericaAgent-<version>-win7-setup.exe`（可选，推荐）
- `SHA256SUMS.txt`
- `release-notes-win7.md`

## 3. 便携版安装（推荐，最快）

1. 下载 `GenericaAgent-<version>-win7-portable.zip`。
2. 校验哈希值（PowerShell）：
   ```powershell
   Get-FileHash .\GenericaAgent-<version>-win7-portable.zip -Algorithm SHA256
   ```
3. 使用 7-Zip 解压到无中文路径目录，例如：`D:\Apps\GenericaAgent`。
4. 首次运行 `GenericaAgent.exe`。
5. 若杀软拦截，按发布说明将目录加入白名单后重试。

### 便携目录建议结构

```text
GenericaAgent/
  GenericaAgent.exe
  portable.ini
  data/
  logs/
  cache/
```

## 4. 安装包安装（可选）

1. 右键以管理员身份运行 `GenericaAgent-<version>-win7-setup.exe`。
2. 按向导完成安装，默认路径：`C:\Program Files\GenericaAgent`。
3. 首次启动后确认主界面可打开。

## 5. 示例任务验证（验收必做）

> 标准：新机器 15 分钟内完成。

1. 打开程序后创建任务 `hello-win7`。
2. 输入示例提示词：
   - `请输出一个包含 3 条待办事项的 Markdown 列表。`
3. 点击执行，确认输出成功。
4. 在 `logs/` 中确认存在当日日志文件。
5. 记录从解压/安装到示例成功的总耗时（分钟）。

## 6. 打包命令（发布人员）

> 在准备好 Win7 兼容二进制文件（放到 `dist/app/`）后执行。

### 6.1 生成便携包

```powershell
powershell -ExecutionPolicy Bypass -File scripts/win7/build-portable.ps1 -Version 1.0.0
```

### 6.2 生成安装包

```powershell
powershell -ExecutionPolicy Bypass -File scripts/win7/build-installer.ps1 -Version 1.0.0
```

## 7. 验收清单（安装侧）

- [ ] 便携包可在 Win7 SP1 新机器解压即用。
- [ ] 安装包可在 Win7 SP1 正常安装与卸载。
- [ ] 示例任务可成功执行并生成日志。
- [ ] 从开始到示例成功 ≤ 15 分钟。
