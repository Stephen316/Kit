from convert.Formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    KVertedgeCap,
)

# the attribute names order must stay explicit so inconsistent revision links fail before history reconstruction
KAttribNames = (
    "ATTRIB_CUSTOM-attrib",
    "stitch_hint-sys-attrib",
    "vertedge-sys-attrib",
    "no_merge_attribute-st-attrib",
    "name_attrib-gen-attrib",
    "int64_attrib-name_attrib-gen-attrib",
)

# the coedge uses order must stay explicit so inconsistent revision links fail before history reconstruction
KCoedgeUses = ("coedge", "tcoedge-coedge")

# the coedge rules vocabulary must stay centralized so journal validation agrees on supported native identities
KCoedgeRules: dict[int, tuple[str, ...]] = {
    0: KAttribNames,
    2: (),
    3: KCoedgeUses,
    4: KCoedgeUses,
    5: KCoedgeUses,
    6: ("edge", "tedge-edge"),
    8: ("loop", "wire"),
    10: ("pcurve",),
}

# the edge rules vocabulary must stay centralized so journal validation agrees on supported native identities
KEdgeRules: dict[int, tuple[str, ...]] = {
    0: KAttribNames,
    2: (),
    3: ("vertex", "tvertex-vertex"),
    5: ("vertex", "tvertex-vertex"),
    7: KCoedgeUses,
    8: ("ellipse-curve", "straight-curve", "intcurve-curve"),
}

# the vertex rules vocabulary must stay centralized so journal validation agrees on supported native identities
KVertexRules: dict[int, tuple[str, ...]] = {
    0: KAttribNames,
    2: (),
    3: ("edge", "tedge-edge"),
    5: ("point",),
}

# the vertedge rules vocabulary must stay centralized so journal validation agrees on supported native identities
KVertedgeRules: dict[int, tuple[str, ...]] = {
    0: (),
    2: KAttribNames,
    3: KAttribNames,
    4: ("vertex", "tvertex-vertex"),
    **{6 + 2 * SlotIndex: ("edge", "tedge-edge") for SlotIndex in range(KVertedgeCap)},
}

# the entity reference rules vocabulary must stay centralized so journal validation agrees on supported native identities
KEntityRefRules: dict[str, dict[int, tuple[str, ...]]] = {
    "transform": {0: KAttribNames},
    "asmheader": {0: KAttribNames},
    "body": {
        0: KAttribNames,
        2: (),
        3: ("lump",),
        4: (),
        5: ("transform",),
    },
    "lump": {
        0: KAttribNames,
        2: (),
        3: ("lump",),
        4: ("shell",),
        5: ("body",),
    },
    "shell": {
        0: KAttribNames,
        2: (),
        3: ("shell",),
        4: (),
        5: ("face",),
        6: ("wire",),
        7: ("lump",),
    },
    "wire": {
        0: KAttribNames,
        2: (),
        3: ("wire",),
        4: KCoedgeUses,
        5: ("shell",),
        6: (),
    },
    "face": {
        0: KAttribNames,
        2: (),
        3: ("face",),
        4: ("loop",),
        5: ("shell",),
        6: (),
        7: (
            "plane-surface",
            "cone-surface",
            "sphere-surface",
            "torus-surface",
            "spline-surface",
        ),
    },
    "loop": {
        0: KAttribNames,
        2: (),
        3: ("loop",),
        4: ("coedge", "tcoedge-coedge"),
        5: ("face",),
    },
    "coedge": KCoedgeRules,
    "tcoedge-coedge": {**KCoedgeRules, 13: ()},
    "edge": KEdgeRules,
    "tedge-edge": KEdgeRules,
    "vertex": KVertexRules,
    "tvertex-vertex": KVertexRules,
    "spline-surface": {0: KAttribNames, 2: ()},
    "intcurve-curve": {0: KAttribNames, 2: ()},
    "pcurve": {0: KAttribNames, 2: (), 4: ("intcurve-curve",)},
    "point": {0: KAttribNames, 2: ()},
    "plane-surface": {0: KAttribNames, 2: ()},
    "sphere-surface": {0: KAttribNames, 2: ()},
    "torus-surface": {0: KAttribNames, 2: ()},
    "cone-surface": {0: KAttribNames, 2: ()},
    "ellipse-curve": {0: KAttribNames, 2: ()},
    "straight-curve": {0: KAttribNames, 2: ()},
    "ATTRIB_CUSTOM-attrib": {
        0: ("ATTRIB_CUSTOM-attrib",),
        2: KAttribNames,
        3: KAttribNames,
        4: (
            "body",
            "face",
            "edge",
            "coedge",
            "tedge-edge",
            "tcoedge-coedge",
        ),
    },
    "stitch_hint-sys-attrib": {
        0: (),
        2: KAttribNames,
        3: KAttribNames,
        4: ("edge", "tedge-edge"),
    },
    "vertedge-sys-attrib": KVertedgeRules,
    "no_merge_attribute-st-attrib": {
        0: (),
        2: KAttribNames,
        3: KAttribNames,
        4: ("edge", "tedge-edge"),
    },
    "name_attrib-gen-attrib": {
        0: (),
        2: KAttribNames,
        3: KAttribNames,
        4: ("edge",),
    },
    "int64_attrib-name_attrib-gen-attrib": {
        0: (),
        2: KAttribNames,
        3: KAttribNames,
        4: ("face",),
    },
}
