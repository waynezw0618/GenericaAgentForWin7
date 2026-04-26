# 关键依赖版本钉死说明

为确保 Windows 7 SP1 兼容，关键依赖必须钉死版本，禁止范围约束。

## 规则

- 允许：`package==1.2.3`
- 不允许：`package>=1.2.3`、`package^1.2.3`、`package~1.2.3`
- 必须提交 lockfile 或等效的完整版本清单。

## 当前基线

- 运行时：Python 3.8.10
- pip：23.0.1
- VC++ Redistributable：14.29.30139
- OpenSSL：1.1.1 系列

## 变更流程

1. 先在分支中更新依赖版本清单。
2. 在 Win7 SP1（x64/x86）执行 preflight + smoke。
3. 通过后再合并。
