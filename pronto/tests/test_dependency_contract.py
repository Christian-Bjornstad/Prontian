"""Prevent dependency updates from leaving manifests and universal locks inconsistent."""

import json

import pytest

from scripts.check_dependencies import check_dependencies


@pytest.fixture
def dependency_repo(tmp_path):
    (tmp_path / "requirements-desktop.txt").write_text("-r requirements.txt\nPyQt6==6.11.0\n")
    (tmp_path / "requirements.txt").write_text("reportlab==5.1.0\n")
    (tmp_path / "requirements-dev.txt").write_text(
        "-r requirements-desktop.txt\n-r requirements-browser.txt\n"
    )
    (tmp_path / "requirements-browser.txt").write_text("playwright==1.64.1\n")
    (tmp_path / "requirements-lock.txt").write_text(
        "reportlab==5.1.0\npyqt6==6.11.0\npyqt6-qt6==6.11.2\n"
    )
    (tmp_path / "requirements-dev-lock.txt").write_text(
        "reportlab==5.1.0\npyqt6==6.11.0\npyqt6-qt6==6.11.2\nplaywright==1.64.1\npyee==14.0.0\n"
    )
    (tmp_path / "package.json").write_text(json.dumps({"devDependencies": {"jsdom": "31.0.0"}}))
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "packages": {
                    "": {"devDependencies": {"jsdom": "31.0.0"}},
                    "node_modules/jsdom": {"version": "31.0.0"},
                }
            }
        )
    )
    return tmp_path


def test_consistent_dependencies_accept_generated_transitives(dependency_repo):
    assert check_dependencies(dependency_repo) == []


def test_catches_the_merged_jsdom_manifest_lock_mismatch(dependency_repo):
    (dependency_repo / "package.json").write_text(
        json.dumps({"devDependencies": {"jsdom": "30.1.3"}})
    )
    assert any("jsdom" in issue for issue in check_dependencies(dependency_repo))


def test_direct_browser_upgrade_requires_matching_dev_lock(dependency_repo):
    (dependency_repo / "requirements-browser.txt").write_text("playwright==1.65.0\n")
    assert any(
        "playwright" in issue and "requirements-dev-lock" in issue
        for issue in check_dependencies(dependency_repo)
    )


def test_qt_runtime_and_development_must_resolve_to_same_version(dependency_repo):
    lock = dependency_repo / "requirements-dev-lock.txt"
    lock.write_text(lock.read_text().replace("pyqt6-qt6==6.11.2", "pyqt6-qt6==6.12.0"))
    assert any("pyqt6-qt6" in issue for issue in check_dependencies(dependency_repo))


def test_conflicting_direct_includes_do_not_silently_choose_a_version(dependency_repo):
    (dependency_repo / "requirements-browser.txt").write_text(
        "reportlab==4.4.10\nplaywright==1.64.1\n"
    )
    assert any("reportlab" in issue for issue in check_dependencies(dependency_repo))
