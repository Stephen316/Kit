from __future__ import annotations

from tools.TestShards.Reuse.Select.ReuseChoice import ReuseChoice


def DescribeReuse(Choice: ReuseChoice) -> str:
    if not Choice.Outcomes:
        return f"No test results were reused because {Choice.Reason}.\n"
    return (
        f"{len(Choice.Outcomes)} tests in {len(Choice.Entries)} modules reuse results "
        f"that merge-group run {Choice.Run} verified, because their recorded dependencies did not change.\n"
    )
