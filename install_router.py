#!/usr/bin/env python3
"""Preview/install only the reviewed workspace-router skill. Python 3.10+."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

NAME = "workspace-router"
REQUIRED = {"SKILL.md", "agents/openai.yaml", "scripts/router.py", "references/policy.json",
            "references/protocol.md", "references/workspaces.md", "references/maintenance.md"}


def linked(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def manifest(root):
    if not root.is_dir() or linked(root):
        raise ValueError("source/target must be an ordinary directory")
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in dirs + files:
            if linked(base / name):
                raise ValueError("linked package entries are not supported")
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(".pyc"):
                continue
            path = base / name
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def under(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def install(source, codex_home, *, apply=False, replace=False):
    source = Path(source).absolute()
    if linked(source):
        raise ValueError("source must not be a link")
    source = source.resolve()
    home = Path(codex_home).resolve()
    skills = home / "skills"
    backup_root = home / "router-backups"
    for folder in (skills, backup_root):
        if linked(folder) or not under(folder.resolve(), home):
            raise ValueError("installation parent escapes Codex home")
    target = skills / NAME
    if linked(target):
        raise ValueError("target must not be a link")
    if under(source, target) or under(target, source):
        raise ValueError("source and target must not overlap")
    expected = manifest(source)
    if not REQUIRED.issubset(expected):
        raise ValueError("package is incomplete")
    existing = manifest(target) if target.exists() else None
    report = {"source": str(source), "target": str(target), "files": len(expected),
              "action": "unchanged" if existing == expected else "replace" if existing else "install",
              "applied": False, "backup": None}
    if not apply or report["action"] == "unchanged":
        return report
    if existing is not None and not replace:
        raise ValueError("existing content differs; review and use --replace to back up and replace")
    # Stage outside skill discovery. No recursive deletion is performed.
    backup_root.mkdir(parents=True, exist_ok=True)
    stage = backup_root / ("staging-" + uuid.uuid4().hex)
    stage.mkdir()
    for relative in expected:
        dest = stage / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, dest)
    if manifest(stage) != expected:
        raise ValueError("staged package differs; install cancelled")
    skills.mkdir(parents=True, exist_ok=True)
    # Detect concurrent changes before switching; no multi-process installation guarantee.
    if (manifest(target) if target.exists() else None) != existing:
        raise ValueError("target changed during staging; install cancelled")
    backup = None
    if existing is not None:
        backup = backup_root / ("workspace-router-" + uuid.uuid4().hex)
        target.rename(backup)
    try:
        stage.rename(target)
    except OSError:
        if backup is not None and not target.exists():
            backup.rename(target)
        raise
    report.update(applied=True, backup=str(backup) if backup else None)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / NAME)
    p.add_argument("--codex-home", type=Path,
                   default=Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))))
    p.add_argument("--install", action="store_true", help="Without this flag, preview only")
    p.add_argument("--replace", action="store_true", help="Back up a changed existing installation first")
    args = p.parse_args()
    try:
        print(json.dumps(install(args.source, args.codex_home, apply=args.install, replace=args.replace),
                         ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(json.dumps({"installed": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
