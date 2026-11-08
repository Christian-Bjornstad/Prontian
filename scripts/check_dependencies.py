"""Check exact input pins against universal locks before installing any dependencies.

This standard-library gate catches manifest drift; pip still resolves and checks
the actual installed dependency graph. It neither downloads nor imports packages.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"([A-Za-z0-9_.-]+)==([^;\s]+)(?:\s*;.*)?")


def _pins(path, seen=None):
    """Follow local -r includes and reject conflicting exact pins across input files."""
    path = path.resolve()
    seen = set() if seen is None else seen
    if path in seen:
        raise ValueError(f"Circular requirements include: {path.name}")
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        text = line.split(" #", 1)[0].strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("-r "):
            values = _pins(path.parent / text[3:].strip(), seen | {path})
        else:
            match = PIN.fullmatch(text)
            if not match:
                raise ValueError(f"Expected an exact dependency pin in {path.name}: {text}")
            name = re.sub(r"[-_.]+", "-", match[1]).lower()
            values = {name: match[2]}
        for name, version in values.items():
            if name in result and result[name] != version:
                raise ValueError(f"Conflicting {name} input pins in {path.name}")
            result[name] = version
    return result


def check_dependencies(root=ROOT):
    """Return actionable input/lock drift, including shared runtime and npm roots.

    The universal lock contract uses one exact version per normalized package
    name; platform markers control installation without selecting other versions.
    Development must include the same complete runtime graph used by installers.
    """
    root = Path(root)
    failures = []
    locks = {}
    for source, lock in (
        ("requirements-desktop.txt", "requirements-lock.txt"),
        ("requirements-dev.txt", "requirements-dev-lock.txt"),
    ):
        try:
            inputs, resolved = _pins(root / source), _pins(root / lock)
        except (ValueError, OSError) as error:
            failures.append(str(error))
            continue
        locks[lock] = resolved
        for name, version in inputs.items():
            if resolved.get(name) != version:
                failures.append(f"{lock}: {name} must match {source} ({version}); regenerate locks")
    if len(locks) == 2:
        runtime, development = locks.values()
        for name, version in runtime.items():
            if development.get(name) != version:
                failures.append(f"Runtime/development lock mismatch: {name}=={version}")
    manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    packages = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))["packages"]
    for group in ("dependencies", "devDependencies"):
        declared, locked = manifest.get(group, {}), packages[""].get(group, {})
        for name in declared.keys() | locked.keys():
            version = declared.get(name)
            if (
                version != locked.get(name)
                or packages.get("node_modules/" + name, {}).get("version") != version
            ):
                failures.append(
                    f"package-lock.json: {name} differs from package.json; run npm install --ignore-scripts"
                )
    return failures


def main():
    """Fail early with every mismatch so a PR can repair the whole dependency update."""
    failures = check_dependencies()
    if failures:
        print("Dependency input/lock mismatch:\n" + "\n".join(failures))
        return 1
    print("Dependency manifests and runtime/development locks agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
