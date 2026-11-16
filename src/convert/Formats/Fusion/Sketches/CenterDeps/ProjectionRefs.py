from dataclasses import dataclass as MakeDataClass


# origin projection keeps its two source routes and distinct output identity
@MakeDataClass(frozen=True, slots=True)
class ProjectionRefs:
    OutputId: int
    SourceId: int
    Records: tuple[int, ...]
