from dataclasses import fields as RecordFields
from typing import Protocol, TypeAlias, Union
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendParts import (
    BlendFrame,
    BlendSupport,
    InterpRadius,
    InterpSample,
    OffsetRadius,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendRecords import (
    GtwoBlend,
    SrfSrfBlend,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    CurveContext,
    ExactIntCur,
    ExpParCur,
    IntIntCur,
    ParIntCur,
    SpringIntCur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.LoftRecords import (
    LoftPiece,
    LoftSection,
    LoftSplSur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    ExactSplSur,
    SplineCommon,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepPaths import (
    LawPath,
    NormalPath,
    PathHead,
    RailPath,
    TwistPath,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepRecords import (
    SweepProfile,
    SweepSur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.VertexRecords import (
    VblBoundary,
    VblSurf,
)

KTypedRecord: TypeAlias = Union[
    CurveContext,
    ExpParCur,
    ExactIntCur,
    ParIntCur,
    IntIntCur,
    SpringIntCur,
    SplineCommon,
    ExactSplSur,
    BlendSupport,
    OffsetRadius,
    InterpSample,
    InterpRadius,
    BlendFrame,
    SrfSrfBlend,
    GtwoBlend,
    VblBoundary,
    VblSurf,
    PathHead,
    LawPath,
    RailPath,
    NormalPath,
    TwistPath,
    SweepProfile,
    SweepSur,
    LoftPiece,
    LoftSection,
    LoftSplSur,
]

KRecordTypes = (
    CurveContext,
    ExpParCur,
    ExactIntCur,
    ParIntCur,
    IntIntCur,
    SpringIntCur,
    SplineCommon,
    ExactSplSur,
    BlendSupport,
    OffsetRadius,
    InterpSample,
    InterpRadius,
    BlendFrame,
    SrfSrfBlend,
    GtwoBlend,
    VblBoundary,
    VblSurf,
    PathHead,
    LawPath,
    RailPath,
    NormalPath,
    TwistPath,
    SweepProfile,
    SweepSur,
    LoftPiece,
    LoftSection,
    LoftSplSur,
)


class RecordBuilder(Protocol):
    def __call__(self, *Parts: KGrammarValue) -> KTypedRecord:
        raise TypeError("a concrete typed subtype record constructor is required")


def RecordParts(Value: KTypedRecord) -> tuple[KGrammarValue, ...]:
    return tuple(getattr(Value, Field.name) for Field in RecordFields(Value))


def RebuildRecord(
    Value: KTypedRecord, Parts: tuple[KGrammarValue, ...]
) -> KTypedRecord:
    if len(Parts) != len(RecordFields(Value)):
        raise ValueError("Fusion typed subtype record lost a field")
    Builder = CastValue(RecordBuilder, type(Value))
    return Builder(*Parts)
