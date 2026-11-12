from dataclasses import dataclass as MakeDataClass

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# ordered source targets retain their exact authored controls and evaluated branch
@MakeDataClass(frozen=True, slots=True)
class PlaneRevTarget:
    PlaneId: str
    StepId: str
    AngleParamId: str
    AngleRadians: float
    OffsetParamId: str
    RotationAxis: SpaceVector
    ZeroFrame: Transform
    RootTurns: int
    SweepSign: int
