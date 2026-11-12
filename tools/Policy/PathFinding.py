from __future__ import annotations

from dataclasses import dataclass as DataClass


# shared findings keep command output and focused tests ordered by one stable contract
@DataClass(frozen=True, order=True, slots=True)
class PathFinding:
    RepoPath: str
    RuleCode: str
    MessageText: str
