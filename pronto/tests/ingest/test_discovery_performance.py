"""Discovery keeps exact source identity while bounding filesystem work."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from pronto_ingest.discovery import discover_folders, regular_file
from scripts.benchmark_discovery import RUN, build_fixture, measure


def test_metadata_round_trips_are_bounded_per_source_file(tmp_path):
    """Avoid repeatedly checking every ancestor of each already-scanned file.

    A count budget is deterministic on local and network disks. Eight lstat
    calls per file allows independent file checks and linkage validation; it
    rules out work proportional to the depth of every candidate's ancestors.
    """
    folders = build_fixture(tmp_path, samples=12)
    file_count = sum(1 for folder in folders for path in folder.rglob("*") if path.is_file())
    result = measure(folders)
    assert result["reports"] == 12
    assert result["path_calls"].get("lstat", 0) <= file_count * 8


def test_many_samples_keep_reviewed_variants_in_exact_sample_scope(tmp_path):
    folders = build_fixture(tmp_path, samples=12)
    plan = discover_folders(folders)
    assert plan.run_ids == (RUN,)
    assert len(plan.reports) == 12
    assert all(report.ready and report.report_version == "qc" for report in plan.reports)
    for report in plan.reports:
        assert report.files["variants"] == (
            folders[1] / report.sample_id / f"{report.sample_id}_small_variant_table_forQC.tsv",
        )
        assert report.files["sample_list"] == (folders[0] / report.sample_id / "sample_list.tsv",)
        assert report.files["cnv_table"][0].parent.name == report.sample_id


def test_new_scan_observes_changed_metadata_and_source_signatures(tmp_path):
    """A faster scan must not keep a process-wide cache of stale source data."""
    folders = build_fixture(tmp_path, samples=1)
    first = discover_folders(folders)
    source = first.reports[0].files["variants"][0]
    source.write_bytes(source.read_bytes() + b"\n")
    metadata = folders[0] / "InPreD_PRONTO_metadata_tsoppi.txt"
    metadata.write_text(metadata.read_text().replace("\tY\n", "\tNO\n"), encoding="utf-8")
    second = discover_folders(folders)
    assert first.reports[0].selected
    assert not second.reports[0].selected
    assert second.source_signatures[source][0] == first.source_signatures[source][0] + 1


def test_selected_root_with_windows_reparse_flag_is_rejected(tmp_path, monkeypatch):
    """Junction rejection is required even when the target is a regular folder."""
    folders = build_fixture(tmp_path, samples=1)
    original = Path.lstat

    def reparse_root(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == folders[0]:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=getattr(info, "st_file_attributes", 0) | 0x400,
            )
        return info

    monkeypatch.setattr(Path, "lstat", reparse_root)
    with pytest.raises(ValueError, match="lenker"):
        discover_folders(folders)


def test_independent_file_validation_does_not_reuse_a_stale_parent_check(tmp_path, monkeypatch):
    """Import must recheck path safety after a completed discovery scan."""
    folders = build_fixture(tmp_path, samples=1)
    source = discover_folders(folders).reports[0].files["variants"][0]
    assert regular_file(source)
    original = Path.lstat

    def changed_parent(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if path == source.parent:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_file_attributes=getattr(info, "st_file_attributes", 0) | 0x400,
            )
        return info

    monkeypatch.setattr(Path, "lstat", changed_parent)
    assert not regular_file(source)
