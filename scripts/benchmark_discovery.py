"""Measure folder discovery with disposable, entirely synthetic sequencing runs.

Run from the repository root with ``python scripts/benchmark_discovery.py``.
The fixture is generated outside the checkout and deleted on completion. Counts
of Path metadata calls expose network-filesystem round trips without assuming
that local wall-clock timings predict SMB/Citrix performance.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUN = "261001_A00001_0001_ASYNTHETIC"


def build_fixture(root: Path, samples: int = 30) -> tuple[Path, ...]:
    """Create exact run/sample scopes with raw and reviewed variant tables.

    Every sample has an independent DNA-only sample_list, CNV table and QC
    image placeholder. Discovery identifies image roles without decoding them;
    this fixture intentionally exercises discovery, not report import.
    """
    raw = root / RUN
    reviewed = root / (RUN + "_report_withQC")
    raw.mkdir(parents=True)
    reviewed.mkdir()
    metadata = ["Sample_id\tSequencing_run_id\tStudy_id\tCreate_report"]
    summary = ["sample_id\tTMB\tMSI"]
    for index in range(samples):
        sample = f"SYN{index:04d}-D01-P01-A01"
        metadata.append(f"{sample}\t{RUN}\tSYNTHETIC\tY")
        summary.append(f"{sample}_P\t3\t0")
        source = raw / sample
        target = reviewed / sample
        source.mkdir()
        target.mkdir()
        variants = (
            "Sample_ID\tGene_symbol\tGenomic_location\tDNA_change\n"
            f"{sample}\tSYNTHETIC\t1:123\tc.1A>G\n"
        )
        (source / f"{sample}_small_variant_table.tsv").write_text(variants, encoding="utf-8")
        (target / f"{sample}_small_variant_table_forQC.tsv").write_text(variants, encoding="utf-8")
        (source / "sample_list.tsv").write_text(
            f"sample_type\tsample_ID\ndna_tumor\t{sample}\n", encoding="utf-8"
        )
        (source / f"{sample}_merged_CNV_summary_FC_sorted.tsv").write_text(
            f"Sample_ID\tGene_Symbol\tChromosome\tGene_Start\n{sample}\tSYNTHETIC\t1\t1\n",
            encoding="utf-8",
        )
        (source / f"{sample}_sample_QC_plot.png").write_bytes(
            b"discovery-only synthetic placeholder"
        )
        # Unsupported files are visible as unassigned, never opened as tables.
        (source / "reads.bam").write_bytes(b"synthetic non-alignment placeholder")
    (raw / "InPreD_PRONTO_metadata_tsoppi.txt").write_text(
        "\n".join(metadata) + "\n", encoding="utf-8"
    )
    (raw / f"{RUN}_variant_summary.tsv").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return raw, reviewed


def measure(folders: tuple[Path, ...]) -> dict:
    """Return timings and Path I/O counters for one uncached discovery call."""
    from pronto_ingest.discovery import discover_folders

    counts = Counter()
    original_lstat, original_stat, original_open = Path.lstat, Path.stat, Path.open

    def counted_lstat(path, *args, **kwargs):
        counts["lstat"] += 1
        return original_lstat(path, *args, **kwargs)

    def counted_stat(path, *args, **kwargs):
        counts["stat"] += 1
        return original_stat(path, *args, **kwargs)

    def counted_open(path, *args, **kwargs):
        counts["open"] += 1
        return original_open(path, *args, **kwargs)

    with (
        patch.object(Path, "lstat", counted_lstat),
        patch.object(Path, "stat", counted_stat),
        patch.object(Path, "open", counted_open),
    ):
        started = time.perf_counter()
        plan = discover_folders(folders)
        elapsed = time.perf_counter() - started
    if not all(report.ready for report in plan.reports):
        raise RuntimeError("Synthetic fixture unexpectedly produced blocked reports.")
    return {"seconds": elapsed, "reports": len(plan.reports), "path_calls": dict(counts)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--repeat", type=int, default=3)
    options = parser.parse_args()
    if not 1 <= options.samples <= 200 or not 1 <= options.repeat <= 20:
        parser.error("Use 1-200 samples and 1-20 repeats.")
    with tempfile.TemporaryDirectory(prefix="prontian-discovery-") as directory:
        folders = build_fixture(Path(directory), options.samples)
        file_count = sum(1 for folder in folders for path in folder.rglob("*") if path.is_file())
        results = [measure(folders) for _ in range(options.repeat)]
    print(
        json.dumps(
            {
                "samples": options.samples,
                "files": file_count,
                "repeat": options.repeat,
                "median_seconds": statistics.median(result["seconds"] for result in results),
                "runs": results,
                "scope": "Synthetic discovery only; local cache and filesystem affect timings. Path.stat includes Path.lstat internals.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
