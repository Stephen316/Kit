import sys as System
from pathlib import Path as FilePath

import pytest as Pytest

from tests.Research.Supervisor.SupervisorClaimTests import WitnessClaimCap


# the warm windows claim helper must preserve the same transactional capacity reason
@Pytest.mark.skipif(System.platform != "win32", reason="Windows process boundary")
def CheckWinCap(TmpPath: FilePath) -> None:
    WitnessClaimCap(TmpPath)
