from __future__ import annotations

from collections import Counter


def DescribeCache(Measured: int, Carried: int, Reasons: Counter[str]) -> str:
    LineList = [
        "## Test cache",
        "",
        f"Recorded {Measured} measured and {Carried} carried test modules for later merge-group candidates.",
    ]
    LineList.extend(
        f"- {Count} modules {Reason}" for Reason, Count in sorted(Reasons.items())
    )
    return "\n".join(LineList) + "\n"
