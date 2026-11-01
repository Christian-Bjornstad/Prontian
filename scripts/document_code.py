"""Generate a complete, deterministic source-file reference from owned code.

Module docstrings explain purpose; top-level declarations provide navigation.
The human code guide explains cross-file decisions. --check detects stale docs
without changing files, so adding or retiring code cannot silently lose coverage.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "code-reference.md"
PACKAGES = ("pronto", "pronto_desktop", "pronto_ingest", "pronto_report", "pronto_web", "scripts")
SUFFIXES = {".py", ".js", ".mjs", ".css", ".html", ".json", ".ps1", ".cmd"}
ASSET_PURPOSES = {
    "eslint.config.js": "Apply recommended JavaScript checks with browser globals to owned report scripts.",
    "report.js": "Workspace tabs, in-memory review edits, command validation, persistence and exports.",
    "working-draft.js": "Integrate the versioned working-draft command protocol with the report UI.",
    "review-v3.js": "Link finding and biomarker controls, section QC and plot navigation for v3 reviews.",
    "review-v4.js": "Unified finding controls, current review fields and manual CNV rows.",
    "table-views.js": "Compact/full tables, source detail indexing and expanded table interaction.",
    "report-igv.js": "Local IGV lifecycle, reference selection, local reads and optional alignment preservation.",
    "report-attribution.js": "Attach current reviewer attribution to print and export actions.",
    "presentation-fields.js": "Manage presentation text and figure fields in editable review state.",
    "report.css": "Report layout, accessible interaction states, dialogs, tables and print styling.",
    "PRONTIAN_START.cmd": "Launch the app through local Python or Python FELLES/Ivanti.",
    "PRONTIAN_INSTALL.cmd": "Install pinned desktop dependencies through the selected Python interpreter.",
    "PRONTIAN_SNARVEI.cmd": "Run the optional Windows shortcut creator.",
    "PRONTIAN_REPARER_TILGANG.cmd": "Explicitly invoke the inherited-ACL repair tool for managed shared data.",
    "create_desktop_shortcut.ps1": "Create a desktop shortcut after checking target, icon, data root and port.",
    "repair_shared_access.ps1": "Inspect/repair eligible owner-created private ACLs with backups and bounded scope.",
    "check_diagrams.mjs": "Parse every maintained Mermaid block using the pinned Mermaid parser.",
}


def source_files() -> list[Path]:
    """Enumerate owned source plus entry points, excluding build/vendor artifacts."""
    paths = [path for name in PACKAGES for path in (ROOT / name).rglob("*")]
    paths += list(ROOT.glob("*.py")) + list(ROOT.glob("*.cmd")) + [ROOT / "eslint.config.js"]
    return sorted(
        {
            path
            for path in paths
            if path.is_file()
            and path.suffix in SUFFIXES
            and "__pycache__" not in path.parts
            and not path.is_relative_to(ROOT / "pronto_report" / "static" / "igv")
        },
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def describe(path: Path) -> tuple[str, str]:
    """Return purpose and navigable declarations; never execute application code."""
    relative = path.relative_to(ROOT).as_posix()
    if path.suffix == ".py":
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        doc = ast.get_docstring(tree)
        definitions = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        if "migrations" in path.parts:
            purpose = (
                "Django schema migration: "
                + path.stem.replace("_", " ")
                + ". Preserve applied history."
            )
        elif doc:
            purpose = doc.split("\n\n", 1)[0].replace("\n", " ")
        elif path.name == "__init__.py":
            purpose = (
                "Package boundary for "
                + str(path.parent.relative_to(ROOT)).replace("\\", "/")
                + "."
            )
        elif path.name.startswith("test"):
            purpose = (
                "Behavioral regression coverage: "
                + path.stem.removeprefix("test_").replace("_", " ")
                + "."
            )
        else:
            raise ValueError(f"Add a module-purpose docstring: {relative}")
        tests = [node for node in definitions if node.name.startswith("test_")]
        if tests:
            symbols = f"{len(tests)} top-level test scenarios; " + ", ".join(
                f"`{node.name}`"
                for node in definitions
                if not node.name.startswith("test_") and not node.name.startswith("_")
            )
        else:
            symbols = ", ".join(
                f"[{node.name}](../{relative}#L{node.lineno})"
                for node in definitions
                if not node.name.startswith("_")
            )
        return purpose, symbols.rstrip("; ") or "Package declarations / constants"
    if path.name in ASSET_PURPOSES:
        return ASSET_PURPOSES[path.name], "See source"
    if path.suffix == ".html":
        return "HTML template for " + path.stem.replace("-", " ").replace(
            "_", " "
        ) + ". Rendered by the owning report or Django view.", "Template markup"
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(
            data.get("title")
            or data.get("description")
            or ("Versioned data resource: " + path.name)
        ).split("\n")[0], "JSON Schema / static source data"
    raise ValueError(f"Add a purpose description for {relative}")


def render() -> str:
    """Build the checked-in file map with stable ordering and source links."""
    lines = [
        "# Complete code reference",
        "",
        "Generated by `python scripts/document_code.py`. Do not edit this file directly.",
        "Module purposes come from source docstrings; declarations come from Python AST.",
        "Read [the code guide](code-guide.md) for cross-file workflows and extension points.",
        "",
        "| Source file | Purpose | Public definitions / coverage |",
        "| --- | --- | --- |",
    ]
    for path in source_files():
        relative = path.relative_to(ROOT).as_posix()
        purpose, symbols = describe(path)
        lines.append(
            f"| [{relative}](../{relative}) | {purpose.replace('|', '&#124;')} | {symbols.replace('|', '&#124;')} |"
        )
    lines += [
        "",
        "The bundled `pronto_report/static/igv/igv.esm.min.js` is third-party IGV,",
        "preserved with its upstream LICENSE; edit the owned IGV integration instead.",
        "Binary branding assets are described in `static/branding/README.txt`.",
        "Public input fixtures are documented in [fixture policy](fixture-and-privacy-policy.md).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args()
    expected = render()
    if options.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            parser.exit(1, "Code reference is stale. Run python scripts/document_code.py.\n")
    else:
        OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Code reference: {len(source_files())} source files covered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
