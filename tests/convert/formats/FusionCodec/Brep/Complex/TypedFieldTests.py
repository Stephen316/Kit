from dataclasses import replace as ReplaceValue
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import (
    CreateNurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
    SwapSubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    MapSubtypes,
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendParts import (
    OffsetRadius,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendRecords import (
    SrfSrfBlend,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExactIntCur,
    ExpParCur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.LoftRecords import (
    LoftSplSur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepPaths import (
    LawPath,
    TwistPath,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepRecords import (
    SweepSur,
)
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from tests.convert.formats.FusionCodec.Brep.Complex.ComplexMembers import (
    ComplexMember,
)
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import (
    KNurbsHistory,
    KNurbsStamp,
    NurbsModels,
)

KBlendMember = (
    "re/Fusion/Study/asymmetricfilletflips-b09b81df3c08/swapped_offsets_false.f3d",
    "smbh",
    "2b82d2b4cc4605b991f7d0a74548fd377e385e02e343a41659a179cc8038e0d0",
)
KSweepMember = (
    "re/Fusion/Study/solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d",
    "smbh",
    "d6fc5fbc00178448125739aaf2b60752e322ee9dd64dfebe244de1495f0541d6",
)
KLoftMember = (
    "re/Fusion/Study/lofts-838ea6e83e97/both_direction.f3d",
    "smb",
    "e44db1237dfad4f6d3aaf05bc3a6f5a3d126c5b8eda41e564aa58c206c33d1df",
)


def FindTyped(
    Entities: tuple[KJournalEntity, ...], SubtypeName: str
) -> tuple[int, SubtypeNode]:
    return next(
        (Index, Found)
        for Index, Entity in enumerate(Entities)
        for Found in WalkSubtypes(EntitySubtree(Entity))
        if isinstance(Found, SubtypeNode) and Found.SubtypeName == SubtypeName
    )


def BlendFault(Record: SrfSrfBlend, Fault: str) -> SrfSrfBlend:
    assert isinstance(Record.FirstRadius, OffsetRadius)
    if Fault == "second":
        return ReplaceValue(Record, SecondRadius=None)
    if Fault == "form":
        return ReplaceValue(Record, RadiusForm=0)
    Radius = ReplaceValue(Record.FirstRadius, RadiusKind="interp")
    return ReplaceValue(Record, FirstRadius=Radius)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestBlendFields() -> None:
    Journal = ReadJournal(ComplexMember(*KBlendMember))
    _, Subtype = FindTyped(Journal.Entities, "srf_srf_v_bl_spl_sur")
    Record = Subtype.Body
    assert isinstance(Record, SrfSrfBlend)
    assert Record.Revision == 23100
    assert Record.FirstSupport.SupportKind == "blend_support_surface"
    assert Record.RadiusForm == 1
    First = OffsetRadius("edge_offset", 0, True, 0.0, 3.0, 0.27999999999999997)
    assert Record.FirstRadius == First
    assert Record.SecondRadius == OffsetRadius("edge_offset", 0, True, 0.0, 3.0, 0.12)
    assert Record.Frame.FirstRange == (0.0, 1.0)
    assert Record.Frame.SecondRange == (None, None)
    assert Record.Frame.ReqTolerance == 0.001
    assert Record.Frame.HapCaches == (0, 0, 0)
    assert (Record.Frame.FirstByte, Record.Frame.SecondByte) == (1, 1)
    assert Record.IsConvex and not Record.IsEnvelope
    assert Record.VarBlendSpline is None


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestBlendEdit() -> None:
    Payload = ComplexMember(*KBlendMember)
    Journal = ReadJournal(Payload)
    Index, Subtype = FindTyped(Journal.Entities, "srf_srf_v_bl_spl_sur")
    Record = Subtype.Body
    assert isinstance(Record, SrfSrfBlend)
    assert isinstance(Record.FirstRadius, OffsetRadius)
    assert EntitySubtree(Journal.Entities[Index]) == Subtype
    Radius = ReplaceValue(Record.FirstRadius, OffsetValue=0.5)
    Changed = SubtypeNode(Subtype.SubtypeName, ReplaceValue(Record, FirstRadius=Radius))
    Entities = list(Journal.Entities)
    Entities[Index] = SwapSubtree(Entities[Index], Changed)
    Edited = ReplaceValue(Journal, Entities=tuple(Entities))
    Output = EmitJournal(Edited)
    assert Output != Payload
    assert len(Output) == len(Payload)
    Reread = ReadJournal(Output)
    assert Reread == Edited
    _, Found = FindTyped(Reread.Entities, "srf_srf_v_bl_spl_sur")
    assert isinstance(Found.Body, SrfSrfBlend)
    assert isinstance(Found.Body.FirstRadius, OffsetRadius)
    assert Found.Body.FirstRadius.OffsetValue == 0.5


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("Fault", ("second", "form", "kind"))
def TestBlendFaults(Fault: str) -> None:
    Journal = ReadJournal(ComplexMember(*KBlendMember))
    Index, Subtype = FindTyped(Journal.Entities, "srf_srf_v_bl_spl_sur")
    assert isinstance(Subtype.Body, SrfSrfBlend)
    Broken = SubtypeNode(Subtype.SubtypeName, BlendFault(Subtype.Body, Fault))
    Entities = list(Journal.Entities)
    Entities[Index] = SwapSubtree(Entities[Index], Broken)
    with RaisesError(ValueError):
        _ = EmitJournal(ReplaceValue(Journal, Entities=tuple(Entities)))


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestSweepFields() -> None:
    Journal = ReadJournal(ComplexMember(*KSweepMember))
    _, Subtype = FindTyped(Journal.Entities, "sweep_sur")
    Record = Subtype.Body
    assert isinstance(Record, SweepSur)
    assert Record.ProfileId == -1
    assert not Record.IsOnXy
    assert Record.Profile.ParamRange == (0.25, 0.4)
    assert Record.Profile.PlanarFrame is None
    assert isinstance(Record.Path, TwistPath)
    assert isinstance(Record.Path.InnerPath, LawPath)
    assert Record.Path.Header.PathRange == (0.0, 5.0)
    assert Record.Path.Header.PathCurve.ChoiceKey == "straight"
    assert Record.Path.PathVector == (0.0, 0.0, 1.0)
    assert Record.Path.InnerPath.Formula.ChoiceKey == "VEC(0,0,1)"


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestLoftFields() -> None:
    Geometry = ReadGeometry(ComplexMember(*KLoftMember))
    _, Subtype = FindTyped(Geometry.Entities, "loft_spl_sur")
    Record = Subtype.Body
    assert isinstance(Record, LoftSplSur)
    assert tuple(Section.SectionValue for Section in Record.FirstSections) == (0.0, 1.0)
    assert Record.SecondSections == ()
    assert (Record.FirstRange, Record.SecondRange) == ((1.0, 0.0), (0.0, 1.0))
    assert Record.LoftFlags == (False, False, False, False)
    assert Record.TrailInts == (1, 0)
    Piece = Record.FirstSections[0].Pieces[0]
    assert Piece.PieceKind == 1
    assert Piece.Curve.ChoiceKey == "ellipse"
    assert Piece.SecondPcurve is None
    assert Piece.PieceFlag is False


def TestNurbsFields() -> None:
    Journal = CreateNurbsBody(NurbsModels()[0][1], KNurbsHistory, KNurbsStamp)
    _, Pcurve = FindTyped(Journal.Entities, "exp_par_cur")
    assert isinstance(Pcurve.Body, ExpParCur)
    assert Pcurve.Body.FitTolerance == 0.0
    Carrier = ChoiceValue(
        "spline", (False, SubtypeRef("surface", 0), (None, None, None, None))
    )
    assert Pcurve.Body.Surface == Carrier
    _, Curve = FindTyped(Journal.Entities, "exact_int_cur")
    assert isinstance(Curve.Body, ExactIntCur)
    assert Curve.Body.Context.Revision == 23100
    assert Curve.Body.RangeBounds == (1.0, 0.0)
    assert Curve.Body.Context.FirstSurface == ChoiceValue("null_surface", ())
    assert Curve.Body.Context.Discontinuities == ((), (), ())


def TestRecordWalk() -> None:
    Journal = CreateNurbsBody(NurbsModels()[0][1], KNurbsHistory, KNurbsStamp)
    _, Pcurve = FindTyped(Journal.Entities, "exp_par_cur")
    assert isinstance(Pcurve.Body, ExpParCur)
    assert WalkSubtypes(Pcurve) == (Pcurve, SubtypeRef("surface", 0))
    Mapped = MapSubtypes(Pcurve, {0: 7})
    assert isinstance(Mapped, SubtypeNode)
    assert isinstance(Mapped.Body, ExpParCur)
    assert Mapped.Body.Spline is Pcurve.Body.Spline
    assert Mapped.Body.Surface.Body == (
        False,
        SubtypeRef("surface", 7),
        (None, None, None, None),
    )


def TestPositional() -> None:
    Journal = CreateNurbsBody(NurbsModels()[0][1], KNurbsHistory, KNurbsStamp)
    Index, Pcurve = FindTyped(Journal.Entities, "exp_par_cur")
    assert isinstance(Pcurve.Body, ExpParCur)
    Positional = (Pcurve.Body.Spline, 0.0, Pcurve.Body.Surface)
    Entities = list(Journal.Entities)
    Entities[Index] = SwapSubtree(
        Entities[Index], SubtypeNode("exp_par_cur", Positional)
    )
    with RaisesError(ValueError):
        _ = EmitStateSmb(ReplaceValue(Journal, Entities=tuple(Entities)))
