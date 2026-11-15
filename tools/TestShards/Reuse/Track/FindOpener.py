from __future__ import annotations

import inspect as Inspect
import os as OsLib

from tools.TestShards.Reuse.Track.LocateFile import LocateFile

# self dir must remain consistent across callers so dependency changes cannot revive stale passing results
KSelfDir = OsLib.path.dirname(OsLib.path.abspath(__file__)) + OsLib.sep

# import prefix must remain consistent across callers so dependency changes cannot revive stale passing results
KImportPrefix = "<frozen importlib"

# depth limit needs one explicit bound so test reuse cannot accept inconsistent resource or layout limits
KDepthLimit = 64


# find opener must resolve unambiguously so dependency changes cannot revive stale passing results
def FindOpener(RootText: str) -> tuple[str | None, bool]:
    FrameInfo = Inspect.currentframe()
    Depth = 0
    while FrameInfo is not None and Depth < KDepthLimit:
        FileText = FrameInfo.f_code.co_filename
        if FileText.startswith(KImportPrefix):
            return None, True
        if FileText.endswith(".py") and not FileText.startswith(KSelfDir):
            RelText = LocateFile(RootText, OsLib.path.abspath(FileText))
            if RelText is not None:
                return RelText, False
        FrameInfo = FrameInfo.f_back
        Depth += 1
    return None, False
