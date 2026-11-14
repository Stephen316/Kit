from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import (
    CreateNurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    PcurveSpline,
    SplineSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    CylinderCarrier,
    NurbsBody,
    PlaneCarrier,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsLayout import (
    EdgeRange,
    ModelUses,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from tests.convert.formats.FusionCodec.Brep.Complex.BrokenWider import (
    BrokenWider,
    KWiderFaults,
)
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import (
    KNurbsHistory,
    KNurbsStamp,
)
from tests.convert.formats.FusionCodec.Brep.Complex.WiderNurbs import WiderModels
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive

KWiderRoot = (
    FilePath(__file__).resolve().parents[6]
    / "re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Authored"
)


@TestMarks.parametrize("Label,Model", WiderModels())
def TestWiderAuthor(TmpPath: FilePath, Label: str, Model: NurbsBody) -> None:
    Journal = CreateNurbsBody(Model, KNurbsHistory, KNurbsStamp)
    History = EmitJournal(Journal)
    assert History == (KWiderRoot / (Label + ".smbh")).read_bytes()
    assert JournalArchive(TmpPath / "WiderHistory.zip", History) == Journal
    Payload = EmitStateSmb(Journal)
    assert Payload == (KWiderRoot / (Label + ".smb")).read_bytes()
    Entities = GeometryArchive(TmpPath / "WiderBody.zip", Payload).Entities
    assert Entities == Journal.Entities
    Carriers = tuple(FaceSpec.Surface for FaceSpec in Model.Faces)
    assert sum(isinstance(Value, FaceNode) for Value in Entities) == len(Carriers)
    assert sum(isinstance(Value, LoopNode) for Value in Entities) == sum(
        1 + len(FaceSpec.Holes) for FaceSpec in Model.Faces
    )
    assert sum(isinstance(Value, PlaneNode) for Value in Entities) == sum(
        isinstance(Carrier, PlaneCarrier) for Carrier in Carriers
    )
    assert sum(isinstance(Value, ConeNode) for Value in Entities) == sum(
        isinstance(Carrier, CylinderCarrier) for Carrier in Carriers
    )
    assert tuple(
        SplineSurface(Value.Surface)
        for Value in Entities
        if isinstance(Value, SplineNode)
    ) == tuple(Carrier for Carrier in Carriers if isinstance(Carrier, BsSurface))
    UseSpecs = ModelUses(Model)
    Traced = tuple(UseSpec for UseSpec in UseSpecs if UseSpec.Pcurve is not None)
    Pcurves = tuple(Value for Value in Entities if isinstance(Value, PcurveNode))
    assert tuple(
        PcurveSpline(Value.Curve) for Value in Pcurves if Value.Curve is not None
    ) == tuple(
        NegateCurve(UseSpec.Pcurve) if UseSpec.Reversed else UseSpec.Pcurve
        for UseSpec in Traced
        if UseSpec.Pcurve is not None
    )
    assert tuple((Value.OffsetU, Value.OffsetV) for Value in Pcurves) == tuple(
        (UseSpec.OffsetU, UseSpec.OffsetV) for UseSpec in Traced
    )
    Coedges = tuple(Value for Value in Entities if isinstance(Value, CoedgeNode))
    assert tuple(Value.Pcurve < 0 for Value in Coedges) == tuple(
        UseSpec.Pcurve is None for UseSpec in UseSpecs
    )
    assert tuple(
        (Value.StartParam, Value.EndParam)
        for Value in Entities
        if isinstance(Value, EdgeNode)
    ) == tuple(EdgeRange(EdgeSpec) for EdgeSpec in Model.Edges)


@TestMarks.parametrize("Fault", KWiderFaults)
def TestWiderFault(Fault: str) -> None:
    with RaisesError(ValueError):
        _ = CreateNurbsBody(BrokenWider(Fault), KNurbsHistory, KNurbsStamp)
