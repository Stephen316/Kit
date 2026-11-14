from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import (
    ShellSpec,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    PartSpec,
)

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


@MarkTests.parametrize("Features", KRejected)
def TestPartReject(Features: tuple[KPartFeature, ...]) -> None:
    with RaisesError(ValueError):
        _ = EmitDocument(PartSpec("Rejected", Features))


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
