from __future__ import annotations

from Report.MarkdownText import CommitLink
from SnapshotMarker import BuildMarker


def RenderTrend(
    Snapshot: dict[str, object], History: list[dict[str, object]]
) -> list[str]:
    if not History:
        return []
    return [
        "",
        "<details>",
        "<summary>Reviewable size over recent pushes</summary>",
        "",
        *[
            f"- {CommitLink(Snapshot, Entry['Head'])}: "
            f"{Entry['Totals']['Reviewable']:,} reviewable lines"
            for Entry in [*History[-7:], Snapshot]
        ],
        "",
        "</details>",
    ]


def RenderFooter(
    Snapshot: dict[str, object], History: list[dict[str, object]]
) -> list[str]:
    RunUrl = (
        f"https://github.com/{Snapshot['Repository']}/actions/runs/{Snapshot['RunId']}"
    )
    return RenderTrend(Snapshot, History) + [
        "",
        f"Base {CommitLink(Snapshot, Snapshot['Base'])} · merge base "
        f"{CommitLink(Snapshot, Snapshot['MergeBase'])}",
        f"Classification `{str(Snapshot['RulesVersion'])[:16]}` · trusted "
        f"implementation {CommitLink(Snapshot, Snapshot['Implementation'])}",
        f"[Complete per-file JSON and Markdown]({RunUrl}) · event `{Snapshot['EventId']}`",
        "",
        "</details>",
        "",
        BuildMarker(Snapshot),
    ]
