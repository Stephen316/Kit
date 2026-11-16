from pytest import mark as MarkTests, raises as RaisesError

from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import (
    ShellSpec,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartCases import (
    PartSpec,
)

# the rejected cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRejected: tuple[tuple[KPartFeature, ...], ...] = (
    (ShellSpec(2.0), FilletSpec((40.0, 30.0), 3.0)),
    (FilletSpec((40.0, 30.0), -3.0),),
    (FilletSpec((40.0, 30.0), float("nan")),),
    (FilletSpec((20.0, 30.0), 3.0),),
    (FilletSpec((40.0, 30.0), 35.0),),
    (ChamferSpec((40.0, 30.0), 3.0), ChamferSpec((40.0, 30.0), 3.0)),
    (ShellSpec(20.0),),
    (ShellSpec(16.0),),
    (FilletSpec((40.0, 30.0), 2.0), ShellSpec(3.0)),
    (FilletSpec((40.0, 30.0), 3.0, ""),),
    (ShellSpec(1.0),) * 17,
)


# the part reject contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("Features", KRejected)
def TestPartReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(PartSpec("Rejected", Features))


# the part profile contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize(
    "SpecValue",
    (
        DocumentSpec(
            "Constrained",
            "height",
            20.0,
            "cuboid",
            ConstrainRectangle=True,
            Features=(ShellSpec(2.0),),
        ),
        DocumentSpec(
            "Circular", "height", 20.0, "extrusion", Features=(ShellSpec(2.0),)
        ),
        DocumentSpec("Reserved", "d4", 20.0, "cuboid", Features=(ShellSpec(2.0),)),
    ),
)
def TestPartProfile(SpecValue: DocumentSpec) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(SpecValue)
