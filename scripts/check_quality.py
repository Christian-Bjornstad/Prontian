"""Run deterministic local quality gates; dependency audits/tests run separately."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check_links() -> None:
    """Check repository-local Markdown links and Markdown heading anchors."""
    failures = []
    files = list(ROOT.glob("*.md")) + list((ROOT / "docs").rglob("*.md"))
    for source in files:
        text = re.sub(r"```[\s\S]*?```", "", source.read_text(encoding="utf-8"))
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
            target = target.strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            path = source.parent / unquote(parsed.path) if parsed.path else source
            if not path.exists():
                failures.append(f"{source.relative_to(ROOT)} -> {target}")
            elif parsed.fragment and path.suffix == ".md":
                headings = re.findall(
                    r"^#+\s+(.+)$", path.read_text(encoding="utf-8"), re.MULTILINE
                )
                slugs = {
                    re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
                    for heading in headings
                }
                if unquote(parsed.fragment) not in slugs:
                    failures.append(f"{source.relative_to(ROOT)} -> missing heading {target}")
    if failures:
        raise ValueError("Broken documentation links:\n" + "\n".join(failures))
    print(f"Documentation links: {len(files)} files checked.", flush=True)


def main() -> int:
    """Stop at the first failed gate; return its exit code for local use and CI."""
    npm = shutil.which("npm.cmd" if sys.platform == "win32" else "npm")
    if npm is None:
        raise SystemExit("Install Node.js and run npm ci --ignore-scripts first.")
    commands = [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        [sys.executable, "scripts/document_code.py", "--check"],
        [npm, "run", "lint"],
        [npm, "run", "format:check"],
        [npm, "run", "docs:diagrams"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    check_links()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
