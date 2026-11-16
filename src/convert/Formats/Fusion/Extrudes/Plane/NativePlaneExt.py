from dataclasses import dataclass as Dataclass


# selected plane identity and driving controls remain distinct from the derived extent
@Dataclass(frozen=True, slots=True)
class NativePlaneExt:
    Role: str
    PlaneId: int
    ProxyId: int
    ProfileId: int
    ProfileProxyId: int
    OffsetId: int
    AlongId: int | None
    TaperId: int | None
    Direction: tuple[float, float, float]
    ResultOffset: int
    ComponentId: int
    PlaneFeatureId: int
    EvidenceIds: tuple[int, ...]
