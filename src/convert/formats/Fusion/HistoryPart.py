# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from convert.formats.Fusion.HistoryGroup import HistoryGroup
from interchange.features.FeatureStep import FeatureStep


# each native owner keeps its own chronology and group information
@Dataclass(frozen=True, slots=True)
class HistoryPart:
    HistoryId: int
    OwnerId: int
    EntryIds: tuple[int, ...]
    Groups: tuple[HistoryGroup, ...]
    Steps: tuple[FeatureStep, ...]
