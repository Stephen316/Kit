# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the two one-side chooser caps and their repeated native allocations."""

from PairedCaptureIntake import require
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.Resolved.BossChooser import (
    CheckChoiceOwn,
    ReadChoiceTail,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    ReadFaceReturn,
    ReadSurfaceId,
    SurfaceKey,
)
from convert.adapters.solidworks.Resolved.Scope.BossCap import CheckScopeCap


# A one-arc profile has a single side identity in each chooser face envelope.
def read_radial_face(cursor, kind):
    start = cursor.Offset
    _, _, obj = cursor.TakePointer(("moFaceRef_c",), kind, CompactOnly=True)
    require(
        cursor.ReadInts("<3IiI") == (1, 0, 3, 768, 0),
        "expected one side in the circular chooser face",
    )
    cursor.ReadPoint(2)
    cursor.ReadNull()
    return {"offset": start, "object_index": obj}


# Match each cap and its single native side to the reached profile and active file.
def read_radial_cap(cursor, kind, occurrence):
    face = read_radial_face(cursor, kind)
    primary = ReadSurfaceId(cursor, KCapClass, kind, IsCap=True)
    edge = ReadSurfaceId(cursor, KEdgeClass, kind)
    require(primary["occurrence"] == occurrence, "unexpected circular cap occurrence")
    ReadFaceReturn(cursor)
    return {**face, "end": cursor.Offset, "primary": primary, "edges": [edge]}


# The repeated chooser must point to the existing cap and edge, with no reallocation.
def read_radial_alias(cursor, original):
    face = read_radial_face(cursor, KClassRefKind)
    _, _, cap = cursor.TakePointer((KCapClass,), KObjectRefKind, CompactOnly=True)
    _, _, edge = cursor.TakePointer((KEdgeClass,), KObjectRefKind, CompactOnly=True)
    require(
        (cap, edge)
        == (original["primary"]["object_index"], original["edges"][0]["object_index"]),
        "circular chooser aliases do not reach the original cap and side",
    )
    ReadFaceReturn(cursor)
    return {**face, "end": cursor.Offset, "cap_object": cap, "edge_object": edge}


# Both chooser occurrences must return to the same boss and describe the same centre.
def read_radial_choices(cursor, owner, edge_id):
    require(cursor.ReadInts("<2H") == (1, 1), "expected one circular body chooser")
    _, _, first = cursor.TakePointer(
        ("moPerBodyChooserData_c",), KDefinitionKind, CompactOnly=True
    )
    require(cursor.ReadInts("<H") == (2,), "expected two circular boss caps")
    caps = [
        read_radial_cap(cursor, KDefinitionKind, 0),
        read_radial_cap(cursor, KClassRefKind, 1),
    ]
    _, _, clock, _ = SurfaceKey(caps[0]["primary"])
    ownership = (owner["file_ref_object"], owner["native_feature_id"], clock)
    for cap in caps:
        CheckScopeCap(cap, ownership, (edge_id,))
    centre = ReadChoiceTail(cursor, KDefinitionKind)
    CheckChoiceOwn(cursor, owner)
    require(
        cursor.ReadInts("<3H") == (1, 1, 0), "unexpected secondary circular chooser"
    )
    CheckChoiceOwn(cursor, owner)
    require(
        cursor.ReadInts("<i2H") == (1, 1, 1), "expected one repeated circular chooser"
    )
    _, _, second = cursor.TakePointer(
        ("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True
    )
    require(cursor.ReadInts("<H") == (2,), "expected two circular cap aliases")
    aliases = [read_radial_alias(cursor, cap) for cap in caps]
    repeat = ReadChoiceTail(cursor, KClassRefKind)
    require(
        centre["centre_and_scale"] == repeat["centre_and_scale"],
        "circular chooser centres disagree",
    )
    CheckChoiceOwn(cursor, owner)
    return {
        "primary_object": first,
        "repeated_object": second,
        "caps": caps,
        "cap_aliases": aliases,
        "centre": centre,
        "repeated_centre_object": repeat["centre_object"],
        "end": cursor.Offset,
    }
