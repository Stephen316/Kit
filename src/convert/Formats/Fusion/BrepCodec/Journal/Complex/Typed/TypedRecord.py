from dataclasses import fields as RecordFields
from typing import Protocol, TypeAlias, Union
from typing import cast as CastValue

from convert.Formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendParts import (
    BlendFrame,
    BlendSupport,
    InterpRadius,
    InterpSample,
    OffsetRadius,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendRecords import (
    GtwoBlend,
    SrfSrfBlend,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    CurveContext,
    ExactIntCur,
    ExpParCur,
    IntIntCur,
    ParIntCur,
    SpringIntCur,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.LoftRecords import (
    LoftPiece,
    LoftSection,
    LoftSplSur,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    ExactSplSur,
    SplineCommon,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepPaths import (
    LawPath,
    NormalPath,
    PathHead,
    RailPath,
    TwistPath,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepRecords import (
    SweepProfile,
    SweepSur,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Typed.VertexRecords import (
    VblBoundary,
    VblSurf,
)

# the typed record shape must stay shared so typed journal reconstruction uses one contract for compatible values
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

# the record types order must stay explicit so native geometry variants retain distinct field contracts
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


# the record builder contract needs a dedicated boundary so native geometry variants retain distinct field contracts
class RecordBuilder(Protocol):

    # record builder needs an explicit validity boundary so native geometry variants retain distinct field contracts
    def __call__(self, *Parts: KGrammarValue) -> KTypedRecord:
        raise TypeError("a concrete typed subtype record constructor is required")


# the record parts contract needs a shared interpretation so native geometry variants retain distinct field contracts
def RecordParts(Value: KTypedRecord) -> tuple[KGrammarValue, ...]:
    return tuple(getattr(Value, Field.name) for Field in RecordFields(Value))


# rebuild record needs an explicit validity boundary so native geometry variants retain distinct field contracts
def RebuildRecord(
    Value: KTypedRecord, Parts: tuple[KGrammarValue, ...]
) -> KTypedRecord:
    if len(Parts) != len(RecordFields(Value)):
        raise ValueError("Fusion typed subtype record lost a field")
    Builder = CastValue(RecordBuilder, type(Value))
    return Builder(*Parts)
