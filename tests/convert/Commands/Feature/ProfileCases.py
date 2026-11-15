# contour qualification needs explicit geometric counterexamples that survive neutral document validation
KProfileCases = {
    "OneLine": ((0.0, 0.0), (1.0, 0.0)),
    "OpenChain": ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)),
    "ZeroSide": ((0.0, 0.0), (0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)),
    "Collinear": ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (0.0, 0.0)),
    "Crossed": ((0.0, 0.0), (2.0, 2.0), (0.0, 2.0), (2.0, 0.0), (0.0, 0.0)),
    "LongRing": (
        (0.0, 0.0),
        (2.0, 0.0),
        (3.0, 1.0),
        (1.0, 3.0),
        (-1.0, 1.0),
        (0.0, 0.0),
    ),
    "Disconnected": ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0), (0.0, 0.0)),
    "DuplicateMember": ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0), (0.0, 0.0)),
}

# profile refusal coverage must include unsupported curves and ambiguous groups alongside line contours
KProfileKinds = (
    *KProfileCases,
    "CircleZero",
    "KindMismatch",
    "UnsupportedArc",
    "MultipleLoops",
)
