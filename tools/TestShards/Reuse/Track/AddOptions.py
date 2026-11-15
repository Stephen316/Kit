from __future__ import annotations

import pytest as Pytest


# the options operation needs a consistent construction rule so dependency changes cannot revive stale passing results
def AddOptions(ParserInfo: Pytest.Parser) -> None:
    ParserInfo.addoption(
        "--test-deps",
        dest="TestDeps",
        default=None,
        help="Write the repository files that each test module used to this directory.",
    )
