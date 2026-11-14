from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import (
    CreateNurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    PcurveSpline,
    SplineCurve,
    SplineSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.PatchSheet import (
    BoundaryCurve,
    PatchSheet,
)
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from tests.convert.formats.FusionCodec.Brep.Complex.BrokenNurbs import (
    BrokenNurbs,
    KNurbsFaults,
)
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import (
    BicubicPatch,
    KNurbsHistory,
    KNurbsStamp,
    NurbsModels,
)
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive

KAcceptedRoot = (
    FilePath(__file__).resolve().parents[6] / "re/Fusion/LocalOracle/ComplexGeometry"
)


@TestMarks.parametrize("Label,Model", NurbsModels())
def TestNurbsAuthor(TmpPath: FilePath, Label: str, Model: NurbsBody) -> None:
    Journal = CreateNurbsBody(Model, KNurbsHistory, KNurbsStamp)
    History = EmitJournal(Journal)
    assert History == (KAcceptedRoot / (Label + ".smbh")).read_bytes()
    assert JournalArchive(TmpPath / "NurbsHistory.zip", History) == Journal
    Payload = EmitStateSmb(Journal)
    assert Payload == (KAcceptedRoot / (Label + ".smb")).read_bytes()
    State = GeometryArchive(TmpPath / "NurbsBody.zip", Payload)
    assert State.Entities == Journal.Entities
    Entities = State.Entities
    assert sum(isinstance(Value, FaceNode) for Value in Entities) == len(Model.Faces)
    assert tuple(
        SplineSurface(Value.Surface)
        for Value in Entities
        if isinstance(Value, SplineNode)
    ) == tuple(FaceSpec.Surface for FaceSpec in Model.Faces)
    assert tuple(
        SplineCurve(Value.Curve)
        for Value in Entities
        if isinstance(Value, IntcurveNode)
    ) == tuple(EdgeSpec.Curve for EdgeSpec in Model.Edges)
    Pcurves = tuple(
        PcurveSpline(Value.Curve)
        for Value in Entities
        if isinstance(Value, PcurveNode) and Value.Curve is not None
    )
    assert Pcurves == tuple(
        NegateCurve(UseSpec.Pcurve) if UseSpec.Reversed else UseSpec.Pcurve
        for FaceSpec in Model.Faces
        for UseSpec in FaceSpec.Uses
        if UseSpec.Pcurve is not None
    )


@TestMarks.parametrize("Fault", KNurbsFaults)
def TestNurbsFault(Fault: str) -> None:
    with RaisesError(ValueError):
        _ = CreateNurbsBody(BrokenNurbs(Fault), KNurbsHistory, KNurbsStamp)


def TestNurbsGuards() -> None:
    Surface = BicubicPatch()
    with RaisesError(ValueError):
        _ = CreateNurbsBody(
            ReplaceValue(PatchSheet(Surface), Faces=()), KNurbsHistory, KNurbsStamp
        )
    with RaisesError(ValueError):
        _ = BoundaryCurve(Surface, 4)
    with RaisesError(ValueError):
        _ = PatchSheet(ReplaceValue(Surface, UClosure=1))
    assert BoundaryCurve(Surface, 0).Poles == Surface.Poles[:5]
    assert BoundaryCurve(Surface, 3).Poles == Surface.Poles[::5]
