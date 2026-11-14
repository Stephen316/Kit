from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class LinkKeys:
    LinkId: str
    CacheGuid: str
    DesignToken: int
    ActToken: int
