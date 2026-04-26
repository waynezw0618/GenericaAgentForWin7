from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any



VALID_PERMISSION_SCOPES = {
    "fs.read",
    "fs.write",
    "net.http",
    "proc.exec",
    "ui.notify",
}

SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{1,63}$")


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in lines:
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if not current_list_key:
                raise SkillError(f"skill.yaml 解析失败: 列表项缺少键 -> {line}")
            data[current_list_key].append(line[4:].strip())
            continue
        current_list_key = None
        if ":" not in line:
            raise SkillError(f"skill.yaml 解析失败: 无法解析行 -> {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "[]":
            data[key] = []
        elif value == "":
            data[key] = []
            current_list_key = key
        else:
            data[key] = value
    return data


class SkillError(Exception):
    pass


@dataclass
class SkillManifest:
    name: str
    version: str
    entry: str
    dependencies: list[str]
    permissions: list[str]

    @classmethod
    def load(cls, base_dir: Path) -> "SkillManifest":
        manifest_path = base_dir / "skill.yaml"
        if not manifest_path.exists():
            raise SkillError("缺少必要文件: skill.yaml")

        content = _parse_simple_yaml(manifest_path)

        required_fields = ["name", "version", "entry", "dependencies", "permissions"]
        missing = [field for field in required_fields if field not in content]
        if missing:
            raise SkillError(f"skill.yaml 缺少字段: {', '.join(missing)}")

        name = content["name"]
        version = content["version"]
        entry = content["entry"]
        dependencies = content["dependencies"]
        permissions = content["permissions"]

        if not isinstance(name, str) or not NAME_PATTERN.match(name):
            raise SkillError("name 非法: 仅支持字母开头、长度2-64、可含 - _")

        if not isinstance(version, str) or not SEMVER_PATTERN.match(version):
            raise SkillError("version 非法: 必须为 semver (例如 1.0.0)")

        if not isinstance(entry, str) or not entry.strip():
            raise SkillError("entry 非法: 必须是非空字符串")

        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            raise SkillError("dependencies 非法: 必须是字符串数组")

        if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
            raise SkillError("permissions 非法: 必须是字符串数组")

        overflow = [perm for perm in permissions if perm not in VALID_PERMISSION_SCOPES]
        if overflow:
            raise SkillError(f"权限越界: {', '.join(overflow)}")

        return cls(
            name=name,
            version=version,
            entry=entry,
            dependencies=dependencies,
            permissions=permissions,
        )


def _safe_join(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    root_resolved = root.resolve()
    if os.path.commonpath([str(root_resolved), str(candidate)]) != str(root_resolved):
        raise SkillError(f"非法路径: {relative}")
    return candidate


class SkillManager:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.skills_root = repo_root / ".skills"
        self.registry_path = self.skills_root / "registry.json"
        self.installed_root = self.skills_root / "installed"
        self.skills_root.mkdir(exist_ok=True)
        self.installed_root.mkdir(exist_ok=True)
        if not self.registry_path.exists():
            self.registry_path.write_text("{}", encoding="utf-8")

    def _load_registry(self) -> dict[str, Any]:
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SkillError("registry.json 已损坏")
        return data

    def _save_registry(self, data: dict[str, Any]) -> None:
        self.registry_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _extract_source(self, source: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
        if source.is_dir():
            return source.resolve(), None

        if source.is_file() and source.suffix.lower() == ".zip":
            temp_dir = tempfile.TemporaryDirectory(prefix="skill_import_")
            dst = Path(temp_dir.name)
            with zipfile.ZipFile(source, "r") as zf:
                for member in zf.infolist():
                    member_path = Path(member.filename)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise SkillError(f"压缩包包含非法路径: {member.filename}")
                zf.extractall(dst)
            if (dst / "skill.yaml").exists():
                return dst, temp_dir
            sub_dirs = [item for item in dst.iterdir() if item.is_dir() and (item / "skill.yaml").exists()]
            if len(sub_dirs) == 1:
                return sub_dirs[0], temp_dir
            raise SkillError("zip 中未找到 skill.yaml")

        raise SkillError("仅支持目录或 .zip 技能包")

    def import_skill(self, source: Path) -> str:
        temp_ref: tempfile.TemporaryDirectory[str] | None = None
        try:
            extracted, temp_ref = self._extract_source(source)
            manifest = SkillManifest.load(extracted)
            entry_path = _safe_join(extracted, manifest.entry)
            if not entry_path.exists():
                raise SkillError(f"entry 文件不存在: {manifest.entry}")

            registry = self._load_registry()
            skill_entry = registry.get(manifest.name, {"versions": {}, "active_version": None, "enabled": False})
            if manifest.version in skill_entry["versions"]:
                raise SkillError(f"版本冲突: {manifest.name}@{manifest.version} 已存在")

            install_dir = self.installed_root / manifest.name / manifest.version
            install_dir.parent.mkdir(parents=True, exist_ok=True)
            if install_dir.exists():
                raise SkillError(f"安装目录已存在: {install_dir}")

            rollback_actions: list[tuple[str, Path]] = []
            try:
                shutil.copytree(extracted, install_dir)
                rollback_actions.append(("delete", install_dir))

                skill_entry["versions"][manifest.version] = {
                    "path": str(install_dir.relative_to(self.repo_root)),
                    "entry": manifest.entry,
                    "permissions": manifest.permissions,
                    "dependencies": manifest.dependencies,
                }
                skill_entry["active_version"] = manifest.version
                registry[manifest.name] = skill_entry
                self._save_registry(registry)
            except Exception as exc:  # noqa: BLE001
                for action, target in reversed(rollback_actions):
                    if action == "delete" and target.exists():
                        shutil.rmtree(target)
                raise SkillError(f"导入失败并已回滚: {exc}") from exc

            return f"导入成功: {manifest.name}@{manifest.version}"
        finally:
            if temp_ref:
                temp_ref.cleanup()

    def list_skills(self) -> dict[str, Any]:
        return self._load_registry()

    def enable(self, name: str) -> str:
        registry = self._load_registry()
        if name not in registry:
            raise SkillError(f"技能不存在: {name}")
        registry[name]["enabled"] = True
        self._save_registry(registry)
        return f"已启用: {name}"

    def disable(self, name: str) -> str:
        registry = self._load_registry()
        if name not in registry:
            raise SkillError(f"技能不存在: {name}")
        registry[name]["enabled"] = False
        self._save_registry(registry)
        return f"已禁用: {name}"

    def uninstall(self, name: str) -> str:
        registry = self._load_registry()
        if name not in registry:
            raise SkillError(f"技能不存在: {name}")

        skill_data = registry.pop(name)
        skill_dir = self.repo_root / ".skills" / "installed" / name
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        self._save_registry(registry)
        versions = ", ".join(skill_data["versions"].keys())
        return f"已卸载: {name} (版本: {versions})"

    def rollback(self, name: str) -> str:
        registry = self._load_registry()
        if name not in registry:
            raise SkillError(f"技能不存在: {name}")

        versions = sorted(registry[name]["versions"].keys())
        if len(versions) < 2:
            raise SkillError("无可回滚版本")

        current = registry[name].get("active_version")
        if current not in versions:
            raise SkillError("当前版本记录异常")

        prev_candidates = [v for v in versions if v < current]
        if not prev_candidates:
            raise SkillError("已是最早版本，无法回滚")

        previous = prev_candidates[-1]
        registry[name]["active_version"] = previous
        self._save_registry(registry)
        return f"已回滚: {name} {current} -> {previous}"

    def run(self, name: str) -> str:
        registry = self._load_registry()
        if name not in registry:
            raise SkillError(f"技能不存在: {name}")
        skill_meta = registry[name]
        if not skill_meta.get("enabled"):
            raise SkillError(f"技能未启用: {name}")
        active = skill_meta.get("active_version")
        if not active:
            raise SkillError("无激活版本")
        meta = skill_meta["versions"][active]
        skill_path = self.repo_root / meta["path"]
        entry_file = _safe_join(skill_path, meta["entry"])
        if not entry_file.exists():
            raise SkillError(f"入口脚本丢失: {entry_file}")

        output = subprocess.check_output(["python3", str(entry_file)], text=True)
        return output.strip()
