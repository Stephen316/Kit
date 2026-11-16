# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Encode both ordinary preview members from the generated feature geometry."""

from BossResolve import ResolvedBossState
from OrdinaryProfile import OrdinaryProfile
from PartPreview import (
    DIB_SIZE,
    PNG_SIZE,
    BuildPreviewDrawing,
    Palette,
    RenderPartPreview,
)
from PartPreviews import (
    PREVIEW,
    PREVIEW_PNG,
    EncodeDib,
    EncodePng,
    IndexedPreview,
    RgbaPreview,
)

KNativeResolution = (3779, 3779)


# both native wrappers consume the same fresh geometry and caller colors
def BuildPreviewMembers(
    Generation: int,
    Profile: OrdinaryProfile,
    Boss: ResolvedBossState | None,
    Colors: Palette,
) -> dict[str, bytes]:
    Depth = None
    if Boss is not None:
        Display = Boss.Display
        Depth = abs(Display.DepthMm) / 1000.0
        if Display.Geometry.Reverse:
            Depth = -Depth
    Drawing = BuildPreviewDrawing(
        Profile.Attachment.DatumId,
        Profile.Corners,
        {Line.CreationId: Line.Endpoints for Line in Profile.Lines},
        Depth,
    )
    Rasters = RenderPartPreview(Generation, Drawing, Colors)
    PaletteTable = (*Colors, *((Colors[0],) * (256 - len(Colors))))
    return {
        PREVIEW: EncodeDib(
            Generation, IndexedPreview(*DIB_SIZE, PaletteTable, Rasters.DibIndices)
        ),
        PREVIEW_PNG: EncodePng(
            Generation, RgbaPreview(*PNG_SIZE, KNativeResolution, Rasters.PngRgba)
        ),
    }
