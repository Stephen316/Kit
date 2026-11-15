from __future__ import annotations

from collections.abc import Mapping

# the guard files vocabulary must stay centralized so test reuse agrees on supported native identities
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

# guard prefix must remain consistent across callers so dependency changes cannot revive stale passing results
KGuardPrefix = "tools/TestShards/"


# the compute guard contract needs a shared interpretation so dependency changes cannot revive stale passing results
def ComputeGuard(Blobs: Mapping[str, str], PythonText: str) -> dict[str, object]:
    Guarded = {
        PathText: BlobId
        for PathText, BlobId in sorted(Blobs.items())
        if PathText in KGuardFiles
        or PathText.startswith(KGuardPrefix)
        or PathText.rpartition("/")[2] == "conftest.py"
    }
    return {"Python": PythonText, "Files": Guarded}
