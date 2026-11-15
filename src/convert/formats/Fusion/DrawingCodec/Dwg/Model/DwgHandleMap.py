from dataclasses import dataclass as MakeDataClass


# drawing handle map needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgHandleMap:
    HandleCount: int
    LastHandle: int
    BlockCount: int
