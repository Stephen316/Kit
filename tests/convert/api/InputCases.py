# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.enums.EnumFeatures import BooleanOp, FeatureKind

# saved contrasts distinguish input order from body inventory and creator order
KInputCases = (
    (
        "combinemodes-dcb4956eca6b/cut_multiple.f3d",
        FeatureKind.KBoolean,
        BooleanOp.KCutOperation,
        True,
        (("tool", 354, 322), ("tool", 431, 399), ("target", 275, 243)),
    ),
    (
        "combinemodes-dcb4956eca6b/cut_swapped.f3d",
        FeatureKind.KBoolean,
        BooleanOp.KCutOperation,
        True,
        (("tool", 275, 243), ("target", 354, 322)),
    ),
    (
        "moretools-380212ab6368/CombineCutNoKeep.f3d",
        FeatureKind.KBoolean,
        BooleanOp.KCutOperation,
        False,
        (("tool", 324, 298), ("target", 260, 234)),
    ),
    (
        "bodyselections-62e42366c722/scale_two_bodies_point.f3d",
        FeatureKind.KScale,
        None,
        None,
        (("input", 275, 243), ("input", 354, 322)),
    ),
    (
        "scaleshellinputs-97ef1cfd19e4/shell_two_bodies.f3d",
        FeatureKind.KShell,
        None,
        None,
        (("input", 354, 322), ("input", 275, 243)),
    ),
    (
        "bodyselections-62e42366c722/mirror_two_bodies_plane.f3d",
        FeatureKind.KMirror,
        None,
        None,
        (("input", 275, 243), ("input", 354, 322)),
    ),
)
