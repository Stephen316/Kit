from typing import cast as CastValue

from pytest import approx as ApproxValue, mark as MarkTests

from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from tests.convert.formats.FusionCodec.Documents.PartFeatures.NativeControl import (
    NativeControl,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    PartSpec,
)


@MarkTests.parametrize("NameValue", ("Fillet", "Chamfer", "Shell"))
def TestPartSolid(NameValue: str) -> None:
    _, Stages = SolvePart(PartSpec(NameValue))
    Measured = MeasurePart(Stages[-1].After)
    Native = NativeControl(NameValue)
    assert (Measured.FaceCount, Measured.EdgeCount, Measured.VertexCount) == (
        Native["faces"],
        Native["edges"],
        Native["vertices"],
    )
    assert Measured.VolumeCm == ApproxValue(Native["volume_cm3"], rel=1e-7)
    assert Measured.AreaCm == ApproxValue(Native["area_cm2"], rel=1e-7)
    Lower = CastValue(list[float], Native["min_cm"])
    Upper = CastValue(list[float], Native["max_cm"])
    assert (*Measured.LowerCm, *Measured.UpperCm) == ApproxValue(
        (*Lower, *Upper), abs=1e-7
    )


def TestPartStages() -> None:
    BaseSolid, Stages = SolvePart(PartSpec("MultiFeature"))
    assert [Stage.StateId for Stage in Stages] == [5, 6, 7, 8]
    assert [Stage.Operations for Stage in Stages] == [
        (303,),
        (304,),
        (305,),
        (306, 307),
    ]
    assert Stages[0].Before == BaseSolid
    Volumes = [MeasurePart(Stage.After).VolumeCm for Stage in Stages]
    assert Volumes == sorted(Volumes, reverse=True)
