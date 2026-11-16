# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import KDimensionSpecs

# only the measured native radius and diameter schemas qualify for this read path
KRadialSpecs = {
    "FusionSketchDiameterDim": (0x10000, KDimensionSpecs[0x10000]),
    "FusionSketchRadialDim": (0x20000, KDimensionSpecs[0x20000]),
}
