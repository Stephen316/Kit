from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarRule import (
    KGrammarRule,
    PeekRule,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.RuleWords import (
    Branch,
    Chain,
    Cross,
    Exact,
    Gated,
    KBoundLeaf,
    KBoundPair,
    KBoundQuad,
    KCurveCall,
    KEnumLeaf,
    KFlagLeaf,
    KIntLeaf,
    KOptionCall,
    KPointLeaf,
    KRealArray,
    KRealLeaf,
    KSpaceCall,
    KSurfaceCall,
    KTextLeaf,
    KVectorLeaf,
    Named,
    Picks,
    Repeat,
)

KNamedRules: dict[str, KGrammarRule] = {
    "surface": Picks(
        13,
        {
            "null_surface": Chain(),
            "plane": Chain(KPointLeaf, KVectorLeaf, KVectorLeaf, KFlagLeaf, KBoundQuad),
            "cone": Chain(
                KPointLeaf,
                KVectorLeaf,
                KVectorLeaf,
                KRealLeaf,
                KBoundPair,
                KRealLeaf,
                KRealLeaf,
                KRealLeaf,
                KFlagLeaf,
                KBoundQuad,
            ),
            "sphere": Chain(
                KPointLeaf, KRealLeaf, KVectorLeaf, KVectorLeaf, KFlagLeaf, KBoundQuad
            ),
            "torus": Chain(
                KPointLeaf,
                KVectorLeaf,
                KRealLeaf,
                KRealLeaf,
                KVectorLeaf,
                KFlagLeaf,
                KBoundQuad,
            ),
            "spline": Chain(KFlagLeaf, Named("surfacescope"), KBoundQuad),
        },
    ),
    "curve": Picks(
        13,
        {
            "null_curve": Chain(),
            "straight": Chain(KPointLeaf, KVectorLeaf, KBoundPair),
            "ellipse": Chain(
                KPointLeaf, KVectorLeaf, KVectorLeaf, KRealLeaf, KBoundPair
            ),
            "degenerate_curve": Chain(KPointLeaf, KBoundPair),
            "intcurve": Chain(KFlagLeaf, Named("curvescope"), KBoundPair),
        },
    ),
    "tail": Branch(
        "enum",
        {
            0: Chain(
                Named("bss"),
                KRealLeaf,
                KRealArray,
                KRealArray,
                KRealArray,
                KRealArray,
                KRealArray,
                KRealArray,
                Exact((11, None)),
            )
        },
    ),
    "context": Chain(
        KIntLeaf,
        Branch(
            "enum",
            {
                0: Chain(
                    KSpaceCall,
                    KRealLeaf,
                    KSurfaceCall,
                    KSurfaceCall,
                    KOptionCall,
                    KOptionCall,
                    KBoundPair,
                    KRealArray,
                    KRealArray,
                    KRealArray,
                    KIntLeaf,
                )
            },
        ),
    ),
    "law": PeekRule(
        (
            (4, KIntLeaf),
            (6, KRealLeaf),
            (19, KPointLeaf),
            (20, KVectorLeaf),
            (
                7,
                Picks(
                    7,
                    {
                        "null_law": Chain(),
                        "EDGE": Chain(KCurveCall, KRealLeaf, KRealLeaf),
                    },
                ),
            ),
        )
    ),
    "formula": Picks(7, {"null_law": Chain()}, Repeat(Named("law"))),
    "railhead": Chain(KFlagLeaf, KCurveCall, KBoundPair, KRealLeaf),
    "rail": Branch(
        "int",
        {
            1: Chain(Named("railhead"), KFlagLeaf, Named("formula"), KFlagLeaf),
            2: Chain(
                Named("railhead"),
                KFlagLeaf,
                KFlagLeaf,
                KCurveCall,
                KBoundPair,
                Cross(KRealLeaf, KRealLeaf),
                KFlagLeaf,
                KFlagLeaf,
                KFlagLeaf,
            ),
            3: Chain(
                Named("railhead"),
                KFlagLeaf,
                KSurfaceCall,
                Exact((11, None)),
                KFlagLeaf,
            ),
            5: Chain(
                Named("railhead"),
                KFlagLeaf,
                Named("rail"),
                KPointLeaf,
                KVectorLeaf,
                KRealLeaf,
                KRealLeaf,
            ),
        },
    ),
    "member": Branch(
        "int",
        {0: Chain(KCurveCall, KOptionCall, KOptionCall, Named("membertail"))},
        Chain(KCurveCall, KSurfaceCall, KOptionCall, KFlagLeaf, Named("membertail")),
    ),
    "membertail": Chain(KIntLeaf, Named("subdata"), Gated(KVectorLeaf)),
    "path": Chain(KCurveCall, Repeat(KSpaceCall), KIntLeaf),
    "section": Repeat(Chain(KRealLeaf, Repeat(Named("member")), Named("path"))),
    "scale": Chain(Repeat(Named("member")), Named("path")),
    "side": Chain(
        KTextLeaf,
        KSurfaceCall,
        KCurveCall,
        KOptionCall,
        KPointLeaf,
        KOptionCall,
        KIntLeaf,
        KOptionCall,
    ),
    "offset": Chain(KEnumLeaf, KFlagLeaf, KRealLeaf, KRealLeaf, KRealLeaf),
    "blend": Picks(
        13,
        {
            "edge_offset": Named("offset"),
            "fixed_width": Named("offset"),
            "interp": Chain(
                KEnumLeaf,
                KFlagLeaf,
                KRealLeaf,
                KRealLeaf,
                KOptionCall,
                KEnumLeaf,
                Repeat(
                    Chain(
                        KRealLeaf,
                        KRealLeaf,
                        KRealLeaf,
                        KRealLeaf,
                        KPointLeaf,
                        KVectorLeaf,
                    )
                ),
            ),
        },
    ),
    "vertexblend": Picks(
        13,
        {
            "pcurve": Chain(
                KFlagLeaf,
                KVectorLeaf,
                KFlagLeaf,
                KFlagLeaf,
                KRealLeaf,
                KSurfaceCall,
                KOptionCall,
                KFlagLeaf,
                KRealLeaf,
            )
        },
    ),
    "bounded": Branch(
        "flag",
        {
            0: KBoundLeaf,
            1: Chain(
                KRealLeaf,
                Branch("flag", {0: Chain(), 1: Chain(KRealLeaf, KSpaceCall)}),
            ),
        },
    ),
}
