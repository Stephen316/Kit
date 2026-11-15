from dataclasses import dataclass as MakeDataClass


# resource info needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class ResourceInfo:
    LinkName: str
    FileName: str
    ContentType: str
    Created: str
    IsInterop: bool = False
