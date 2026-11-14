from dataclasses import replace as ReplaceValue

from pytest import raises as RaisesError

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import (
    CreateNurbsBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.RelinkSubtypes import (
    RelinkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.CheckSubtypes import (
    CheckSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListSubtypes import ListSubtypes
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import (
    KNurbsHistory,
    KNurbsStamp,
    NurbsModels,
)


def TestTableOrder() -> None:
    Journal = CreateNurbsBody(NurbsModels()[0][1], KNurbsHistory, KNurbsStamp)
    Tables = tuple(
        ListSubtypes(Value) for Value in Journal.Entities if ListSubtypes(Value)
    )
    assert Tables == (
        (("exact_spl_sur", None),),
        *((("exp_par_cur", None), ("surface", 0)),) * 4,
        *((("exact_int_cur", None),),) * 4,
    )
    CheckSubtypes(Journal.Entities)
    Whole = tuple(range(len(Journal.Entities)))
    assert RelinkSubtypes(Journal.Entities, Whole) is Journal.Entities


def TestTableInline() -> None:
    Journal = CreateNurbsBody(NurbsModels()[0][1], KNurbsHistory, KNurbsStamp)
    Surface = next(
        Index
        for Index, Value in enumerate(Journal.Entities)
        if isinstance(Value, SplineNode)
    )
    Chosen = tuple(Index for Index in range(len(Journal.Entities)) if Index != Surface)
    with RaisesError(ValueError):
        CheckSubtypes(tuple(Journal.Entities[Index] for Index in Chosen))
    Linked = RelinkSubtypes(Journal.Entities, Chosen)
    Pcurves = tuple(
        ListSubtypes(Value) for Value in Linked if isinstance(Value, PcurveNode)
    )
    assert Pcurves == (
        (("exp_par_cur", None), ("exact_spl_sur", None)),
        *((("exp_par_cur", None), ("surface", 1)),) * 3,
    )
    CheckSubtypes(Linked)


def TestTableFamily() -> None:
    Journal = CreateNurbsBody(NurbsModels()[0][1], KNurbsHistory, KNurbsStamp)
    Geometry = ReadGeometry(EmitStateSmb(Journal))
    Index, Value = next(
        (Index, Value)
        for Index, Value in enumerate(Geometry.Entities)
        if isinstance(Value, SplineNode)
    )
    for Fault in (SubtypeRef("surface", 0), SubtypeRef("curve", 0)):
        Entities = list(Geometry.Entities)
        Entities[Index] = ReplaceValue(Value, Surface=Fault)
        with RaisesError(ValueError):
            _ = EmitGeometry(ReplaceValue(Geometry, Entities=tuple(Entities)))
