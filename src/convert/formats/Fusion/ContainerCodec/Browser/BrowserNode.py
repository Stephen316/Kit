from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class BrowserNode:
    RoleName: str
    ClassName: str
    TargetRole: str | None
    ParentRole: str | None
    StringId: str = ""
