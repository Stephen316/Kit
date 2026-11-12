from dataclasses import dataclass as Dataclass


# native control parsing leaves plane selection and reciprocal binding checks independent
@Dataclass(frozen=True, slots=True)
class PlaneExtFields:
    Role: str
    ProxyId: int
    OffsetId: int
    AlongId: int | None
    TaperId: int
    CacheId: int
    Direction: tuple[float, float, float]
