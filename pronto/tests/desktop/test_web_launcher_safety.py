"""The browser-only launcher must preserve existing keys and migration recovery."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def test_existing_database_without_original_key_is_refused(tmp_path):
    from scripts.start_web import configure

    database = tmp_path / "existing.sqlite3"
    database.touch()
    state = tmp_path / "private"
    with (
        patch("scripts.start_web.STATE", state),
        patch.dict(os.environ),
        patch("sys.path", list(sys.path)),
    ):
        with pytest.raises(ValueError, match="original"):
            configure(str(database), 8771)
    assert not (state / "secret.key").exists()


def test_browser_check_backs_up_before_pending_migrations(tmp_path):
    state = tmp_path / "private"
    state.mkdir()
    (state / "secret.key").write_text("synthetic-existing-key-" * 4, encoding="utf-8")
    database = state / "pronto.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE synthetic_source (value TEXT)")
        connection.execute("INSERT INTO synthetic_source VALUES ('preserved')")
    script = """
import os, sys
from pathlib import Path
from scripts import start_web
start_web.STATE = Path(os.environ['PRONTIAN_TEST_STATE'])
sys.argv = ['start_web.py', '--check']
start_web.main()
"""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PRONTO_") and key != "DJANGO_SETTINGS_MODULE"
    }
    env["PRONTIAN_TEST_STATE"] = str(state)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).parents[3],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    backups = list((state / "backups").glob("*.sqlite3"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as connection:
        assert connection.execute("SELECT value FROM synthetic_source").fetchone() == ("preserved",)
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name='auth_user'"
        ).fetchall()
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name='auth_user'"
        ).fetchone()
