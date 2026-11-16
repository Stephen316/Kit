from __future__ import annotations

import os as OsEnv
import subprocess as Subprocess
import sys as System
import textwrap as Textwrap
from pathlib import Path as FilePath

import pytest as Pytest

# command tests need repository context because migration inputs are checked in assets
KRootPath = FilePath(__file__).resolve().parents[2]


# subprocess collection proves legacy and compliant test names coexist without source aliases
def CheckCollect(TmpPath: FilePath) -> None:
    TestPath = TmpPath / "test_mixed_names.py"
    _ = TestPath.write_text(
        "def test_legacy_name():\n"
        + "    assert True\n\n"
        + "def CheckModern():\n"
        + "    assert True\n",
        encoding="utf-8",
    )
    EnvValues = dict(OsEnv.environ)
    _ = EnvValues.pop("PYTEST_ADDOPTS", None)
    CommandArgs = [
        System.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "--rootdir",
        str(KRootPath),
        "-c",
        str(KRootPath / "pyproject.toml"),
        str(TestPath),
    ]
    ResultInfo = Subprocess.run(
        CommandArgs,
        cwd=KRootPath,
        capture_output=True,
        text=True,
        check=False,
        env=EnvValues,
    )

    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
    assert "::test_legacy_name" in ResultInfo.stdout
    assert "::CheckModern" in ResultInfo.stdout


# subprocess execution proves compliant aliases share builtin values and teardown behavior
def CheckAliases(
    TmpPath: FilePath,
    MonkeyPatch: Pytest.MonkeyPatch,
) -> None:
    ProbePath = KRootPath / "tests" / "test_fixture_aliases_probe.py"
    _ = ProbePath.write_text(
        Textwrap.dedent("""
            def test_fixture_aliases(tmp_path, TmpPath, monkeypatch, MonkeyPatch):
                assert TmpPath is tmp_path
                assert MonkeyPatch is monkeypatch
            """),
        encoding="utf-8",
    )
    MonkeyPatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    EnvValues = dict(OsEnv.environ)
    _ = EnvValues.pop("PYTEST_ADDOPTS", None)
    try:
        ResultInfo = Subprocess.run(
            [System.executable, "-m", "pytest", "-q", str(ProbePath)],
            cwd=KRootPath,
            capture_output=True,
            text=True,
            check=False,
            env=EnvValues,
        )
    finally:
        ProbePath.unlink(missing_ok=True)

    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
    assert "1 passed" in ResultInfo.stdout
