# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditRead.XmlField import EditScalar
from convert.adapters.freecad.Native import NativeObject


# retained kit identity ties each live object back to the embedded fusion entity
def FindEditObject(
    Objects: tuple[NativeObject, ...], Identity: str
) -> NativeObject | None:
    Matches = tuple(
        Value
        for Value in Objects
        if (Property := Value.properties.get("KitId")) is not None
        and any(
            NodeValue.get("value") == Identity
            for NodeValue in Property.findall("./String")
        )
    )
    if not Matches:
        return None
    if (
        len(Matches) != 1
        or EditScalar(Matches[0], "KitId", "App::PropertyString", "String") != Identity
    ):
        raise ValueError(f"FreeCAD editable object identity {Identity} is ambiguous")
    return Matches[0]


# dependent links must select the expected typed object with the original identity
def RequireEditObj(
    Objects: tuple[NativeObject, ...], Identity: str, TypeName: str
) -> NativeObject:
    Match = FindEditObject(Objects, Identity)
    if Match is None or Match.type_id != TypeName:
        raise ValueError(
            f"FreeCAD editable object {Identity} is missing or has the wrong type"
        )
    return Match
