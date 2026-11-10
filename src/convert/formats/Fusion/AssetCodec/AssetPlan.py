# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.AssetCodec.SegmentPlan import SegmentPlan
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import (
    AssetManifest,
    RootManifest,
)


# the active asset always owns one typed plan for each core segment
@MakeDataClass(frozen=True, slots=True)
class AssetPlan:
    RootMeta: RootManifest
    AssetMeta: AssetManifest
    Design: SegmentPlan
    ActPlan: SegmentPlan
    Browser: SegmentPlan
    EmptyConfig: bool = False
