from __future__ import annotations

import re as Regex

KCountPattern = Regex.compile(r"^(\d+)(?:/\d+)? tests? collected\b")


def ReadCollected(OutputText: str) -> tuple[str, ...]:
    LineList = OutputText.splitlines()
    if "" not in LineList:
        raise ValueError("pytest collection output has no summary section")
    Boundary = LineList.index("")
    TestIds = tuple(LineList[:Boundary])
    Counts = [
        int(Found.group(1))
        for LineText in LineList[Boundary:]
        if (Found := KCountPattern.match(LineText)) is not None
    ]
    if len(Counts) != 1:
        raise ValueError("pytest collection output has no single collected count")
    if Counts[0] != len(TestIds) or not TestIds:
        raise ValueError(f"pytest reported {Counts[0]} tests but listed {len(TestIds)}")
    if len(set(TestIds)) != len(TestIds):
        raise ValueError("pytest collection listed duplicate node ids")
    if any("::" not in TestId for TestId in TestIds):
        raise ValueError("pytest collection listed an entry that is not a node id")
    return TestIds
