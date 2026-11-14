from pathlib import Path as FilePath

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

KRepoRoot = FilePath(__file__).resolve().parents[6]
KOracleRoot = KRepoRoot / "re/Fusion/LocalOracle/FeatureAuthoring"
KPartCases: dict[str, tuple[KPartFeature, ...]] = {
    "Fillet": (FilletSpec((40.0, 30.0), 3.0),),
    "Chamfer": (ChamferSpec((40.0, 30.0), 3.0),),
    "Shell": (ShellSpec(2.0),),
    "FilletShell": (FilletSpec((40.0, 30.0), 3.0), ShellSpec(2.0)),
    "MultiFeature": (
        FilletSpec((40.0, 30.0), 3.0, "Corner Round"),
        ChamferSpec((0.0, 0.0), 3.0, "Corner Bevel"),
        FilletSpec((40.0, 0.0), 4.0),
        ShellSpec(2.0, "Hollow"),
    ),
}
KFamilyClasses: dict[type[object], str] = {
    FilletSpec: "DcFilletEdgeFeature",
    ChamferSpec: "DcChamferFeature",
    ShellSpec: "DcShellFeature",
}


def PartSpec(NameValue: str, Features: tuple[KPartFeature, ...] = ()) -> DocumentSpec:
    return DocumentSpec(
        Title="Kit " + NameValue,
        ParamName="height",
        LengthMm=20.0,
        ProfileKind="cuboid",
        SketchName="Base Sketch",
        ExtrusionName="Base Extrude",
        BodyName="Body1",
        WidthMm=40.0,
        DepthMm=30.0,
        Features=Features or KPartCases[NameValue],
    )
