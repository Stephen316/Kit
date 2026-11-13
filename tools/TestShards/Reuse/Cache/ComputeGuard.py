from __future__ import annotations

from collections.abc import Mapping

KGuardFiles = frozenset(
    {
        ".github/workflows/MergeQueue.yml",
        "pyproject.toml",
        "pytest.ini",
        "setup.cfg",
        "tox.ini",
        "uv.lock",
    }
)
KGuardPrefix = "tools/TestShards/"


def ComputeGuard(Blobs: Mapping[str, str], PythonText: str) -> dict[str, object]:
    Guarded = {
        PathText: BlobId
        for PathText, BlobId in sorted(Blobs.items())
        if PathText in KGuardFiles
        or PathText.startswith(KGuardPrefix)
        or PathText.rpartition("/")[2] == "conftest.py"
    }
    return {"Python": PythonText, "Files": Guarded}
