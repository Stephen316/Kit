# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
