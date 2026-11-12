from dataclasses import dataclass as Dataclass

from interchange.enums.EnumFeatures import BooleanOp


# native source records retain their ordered roles before resolving historical bodies
@Dataclass(frozen=True, slots=True)
class BodyInput:
    Role: str
    ProxyId: int
    DescriptorId: int
    AssociationId: int | None = None


# combine controls travel alongside operands without inferring output lifecycle
@Dataclass(frozen=True, slots=True)
class BodyInputs:
    Picks: tuple[BodyInput, ...]
    Operation: BooleanOp | None = None
    KeepTools: bool | None = None
