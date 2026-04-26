from __future__ import annotations

import argparse
import json
from pathlib import Path

from skill_manager import SkillError, SkillManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="技能包管理 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_import = sub.add_parser("import-skill", help="导入技能目录或 zip")
    p_import.add_argument("source", type=str)

    p_enable = sub.add_parser("enable", help="启用技能")
    p_enable.add_argument("name", type=str)

    p_disable = sub.add_parser("disable", help="禁用技能")
    p_disable.add_argument("name", type=str)

    p_uninstall = sub.add_parser("uninstall", help="卸载技能")
    p_uninstall.add_argument("name", type=str)

    p_rollback = sub.add_parser("rollback", help="回滚到上一可用版本")
    p_rollback.add_argument("name", type=str)

    p_run = sub.add_parser("run", help="执行启用技能")
    p_run.add_argument("name", type=str)

    sub.add_parser("list", help="查看技能注册表")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    manager = SkillManager(Path.cwd())

    try:
        if args.cmd == "import-skill":
            print(manager.import_skill(Path(args.source)))
        elif args.cmd == "enable":
            print(manager.enable(args.name))
        elif args.cmd == "disable":
            print(manager.disable(args.name))
        elif args.cmd == "uninstall":
            print(manager.uninstall(args.name))
        elif args.cmd == "rollback":
            print(manager.rollback(args.name))
        elif args.cmd == "run":
            print(manager.run(args.name))
        elif args.cmd == "list":
            print(json.dumps(manager.list_skills(), ensure_ascii=False, indent=2))
        return 0
    except SkillError as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
