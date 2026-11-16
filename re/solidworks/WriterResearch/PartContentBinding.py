# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Connect backward compatibility content to the generated package owners."""

from collections.abc import Mapping
from dataclasses import dataclass

from BossResolve import ResolvedBossState
from ConfigAtomManager import ConfigAtomBinding
from ContentManager import (
    ORDINARY_FLAGS,
    UNSET_DENSITY,
    ContentBody,
    ContentClock,
    ContentState,
    EncodeContentManager,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KUnitProperties = ("SW_UnitsLinear", "SW_UnitSystem", "SW_UnitsMassPropMass")
KContentUnits = {(0, 5, 2): (0, 4, 1), (3, 3, 4): (3, 2, 3)}


# material labels and body visibility belong to the active document settings
@dataclass(frozen=True, slots=True)
class PackageContent:
    MaterialName: str
    MaterialId: str
    BodyVisible: bool | None


# both saved property domains represent the same witnessed document units
def ContentUnits(Information: Mapping[str, str | int]) -> tuple[int, int, int]:
    Fields = tuple(Information.get(Name) for Name in KUnitProperties)
    try:
        return KContentUnits[Fields]
    except KeyError as Error:
        raise ValueError(
            "ordinary content unit combination is outside the witnessed scope"
        ) from Error


# the compatibility folder must reference the actual generated atom and named feature
def BindContentBody(
    Atom: ConfigAtomBinding | None,
    Boss: ResolvedBossState | None,
    Visible: bool | None,
) -> ContentBody | None:
    if Atom is None and Boss is None and Visible is None:
        return None
    if Atom is None or Boss is None or type(Visible) is not bool:
        raise ValueError(
            "compatibility body requires one generated atom and explicit visibility"
        )
    return ContentBody(Atom.AtomId, Boss.Opening.Name, Visible)


# the content manager preserves the same active configuration clock and body map
def EncodePackageContent(
    Generation: int,
    ConfigName: str,
    Clock: ContentClock,
    Information: Mapping[str, str | int],
    Atom: ConfigAtomBinding | None,
    Boss: ResolvedBossState | None,
    Settings: PackageContent,
) -> bytes:
    RequireArch(
        Information.get("SW-Configuration Name"),
        ConfigName,
        "content and information use the same active configuration",
    )
    State = ContentState(
        ConfigName,
        Settings.MaterialName,
        Settings.MaterialId,
        ORDINARY_FLAGS,
        UNSET_DENSITY,
        ContentUnits(Information),
        Clock,
        BindContentBody(Atom, Boss, Settings.BodyVisible),
    )
    return EncodeContentManager(Generation, State)
