from collections.abc import Callable
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.BlendRecords import (
    GtwoFrom,
    GtwoTree,
    RollFrom,
    RollTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExactCurveFrom,
    ExactCurveTree,
    IntCurveFrom,
    IntCurveTree,
    ParCurveFrom,
    ParCurveTree,
    PcurveFrom,
    PcurveTree,
    SpringFrom,
    SpringTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.LoftRecords import (
    LoftFrom,
    LoftTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SurfaceRecords import (
    ExactSheetFrom,
    ExactSheetTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.SweepRecords import (
    SweepFrom,
    SweepTree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.VertexRecords import (
    VertexFrom,
    VertexTree,
)

# the body codec shape must stay shared so typed journal reconstruction uses one contract for compatible values
KBodyCodec: TypeAlias = tuple[
    Callable[[KGrammarValue], KGrammarValue], Callable[[KGrammarValue], KGrammarValue]
]

# the typed codecs vocabulary must stay centralized so typed journal reconstruction agrees on supported native identities
KTypedCodecs: dict[str, KBodyCodec] = {
    "exact_spl_sur": (ExactSheetFrom, ExactSheetTree),
    "exact_int_cur": (ExactCurveFrom, ExactCurveTree),
    "par_int_cur": (ParCurveFrom, ParCurveTree),
    "int_int_cur": (IntCurveFrom, IntCurveTree),
    "spring_int_cur": (SpringFrom, SpringTree),
    "exp_par_cur": (PcurveFrom, PcurveTree),
    "sweep_sur": (SweepFrom, SweepTree),
    "loft_spl_sur": (LoftFrom, LoftTree),
    "srf_srf_v_bl_spl_sur": (RollFrom, RollTree),
    "VBL_SURF": (VertexFrom, VertexTree),
    "g2_blend_spl_sur": (GtwoFrom, GtwoTree),
}


# the type body contract needs a shared interpretation so native geometry variants retain distinct field contracts
def TypeBody(SubtypeName: str, TreeValue: KGrammarValue) -> KGrammarValue:
    Codec = KTypedCodecs.get(SubtypeName)
    return TreeValue if Codec is None else Codec[0](TreeValue)


# the tree body contract needs a shared interpretation so native geometry variants retain distinct field contracts
def TreeBody(SubtypeName: str, BodyValue: KGrammarValue) -> KGrammarValue:
    Codec = KTypedCodecs.get(SubtypeName)
    return BodyValue if Codec is None else Codec[1](BodyValue)
