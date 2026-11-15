from __future__ import annotations

from Report.MarkdownText import EscapeText, FileLink
from Report.ShareCounts import CountLines


# the notable decision must stay consistent so reviewers can distinguish semantic changes from generated noise
def IsNotable(FileItem: dict[str, object]) -> bool:
    return (
        FileItem["Confidence"] == "unclassified"
        or bool(FileItem["Binary"])
        or FileItem["Status"] != "M"
        or CountLines(FileItem) == 0
    )


# the largest row contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
def LargestRow(Snapshot: dict[str, object], FileItem: dict[str, object]) -> str:
    IsBinary = bool(FileItem["Binary"])
    AddText = "binary" if IsBinary else f"+{FileItem['Additions']:,}"
    DelText = "binary" if IsBinary else f"−{FileItem['Deletions']:,}"
    return (
        f"| {FileLink(Snapshot, FileItem)} | {EscapeText(FileItem['Category'])} "
        f"| {EscapeText(FileItem['Status'])} | {AddText} | {DelText} |"
    )


# the notable row contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
def NotableRow(Snapshot: dict[str, object], FileItem: dict[str, object]) -> str:
    OldPath = FileItem["PreviousPath"]
    Origin = f" from {EscapeText(OldPath)}" if OldPath else ""
    return (
        f"- {FileLink(Snapshot, FileItem)}: {EscapeText(FileItem['Status'])}{Origin}, "
        f"{EscapeText(FileItem['Category'])}"
    )


# the render files contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
def RenderFiles(
    Snapshot: dict[str, object], TopCount: int, DetailCount: int
) -> list[str]:
    FileList = Snapshot["Files"]

    # ordering by count lines entry entry path must stay deterministic so diff reporting resolves equivalent inputs consistently
    Largest = sorted(FileList, key=lambda Entry: (-CountLines(Entry), Entry["Path"]))
    Notable = [FileItem for FileItem in FileList if IsNotable(FileItem)]
    RowList = ["", "<details>", "<summary>Largest changed files</summary>", ""]
    RowList += ["| File | Category | Status | Additions | Deletions |"]
    RowList += ["| --- | --- | --- | ---: | ---: |"]
    RowList += [LargestRow(Snapshot, FileItem) for FileItem in Largest[:TopCount]]
    RowList += ["", "</details>", "", "<details>"]
    RowList += [
        "<summary>Unclassified, renamed, deleted, binary and metadata-only files</summary>",
        "",
    ]
    RowList += [NotableRow(Snapshot, FileItem) for FileItem in Notable[:DetailCount]]
    if len(Notable) > DetailCount:
        RowList += [
            f"{len(Notable) - DetailCount:,} more entries are retained in the "
            "complete snapshot artifact."
        ]
    RowList += [] if Notable else ["None."]
    return RowList + ["", "</details>"]
