from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ResourceInfo:
    LinkName: str
    FileName: str
    ContentType: str
    Created: str
    IsInterop: bool = False
