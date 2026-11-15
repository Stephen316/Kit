from dataclasses import dataclass as MakeDataClass


# browser node needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class BrowserNode:
    RoleName: str
    ClassName: str
    TargetRole: str | None
    ParentRole: str | None
    StringId: str = ""
