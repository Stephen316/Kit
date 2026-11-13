from __future__ import annotations

KTotalKeys = (
    "Additions",
    "Deletions",
    "Files",
    "Binary",
    "Reviewable",
    "Excluded",
    "Unclassified",
    "Lines",
)
KBucketKeys = ("Additions", "Deletions", "Files", "Binary")


def SummarizeFiles(FileList: list[dict[str, object]]) -> dict[str, object]:
    Buckets: dict[str, dict[str, object]] = {}
    Totals = dict.fromkeys(KTotalKeys, 0)
    for FileItem in FileList:
        Bucket = Buckets.setdefault(FileItem["Category"], dict.fromkeys(KBucketKeys, 0))
        LineCount = FileItem["Additions"] + FileItem["Deletions"]
        PolicyKey = "Excluded" if FileItem["Policy"] == "excluded" else "Reviewable"
        Bucket.update(
            Policy=FileItem["Policy"],
            Color=FileItem["Color"],
            Additions=Bucket["Additions"] + FileItem["Additions"],
            Deletions=Bucket["Deletions"] + FileItem["Deletions"],
            Files=Bucket["Files"] + 1,
            Binary=Bucket["Binary"] + int(FileItem["Binary"]),
        )
        Totals["Additions"] += FileItem["Additions"]
        Totals["Deletions"] += FileItem["Deletions"]
        Totals["Binary"] += int(FileItem["Binary"])
        Totals["Unclassified"] += int(FileItem["Confidence"] == "unclassified")
        Totals[PolicyKey] += LineCount
    Totals["Files"] = len(FileList)
    Totals["Lines"] = Totals["Additions"] + Totals["Deletions"]
    return {"Totals": Totals, "Categories": dict(sorted(Buckets.items()))}
