from dataclasses import dataclass as MakeDataClass


# link keys needs an explicit state contract so cross document references retain their intended ownership
@MakeDataClass(frozen=True, slots=True)
class LinkKeys:
    LinkId: str
    CacheGuid: str
    DesignToken: int
    ActToken: int
