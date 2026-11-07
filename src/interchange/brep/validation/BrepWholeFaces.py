# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter

from interchange.brep.surfaces.BrepSurfaces import SphereSurface, TorusSurface
from interchange.brep.validation.BrepView import BrepView
from interchange.brep.validation.RingTorusValidate import IsRingTorus
from interchange.brep.validation.SphereValidate import IsFullSphere


# a loopless face is whole only when it uniquely bounds a closed solid shell
def GetWholeFaces(ModelValue: BrepView) -> frozenset[str]:
    Surfaces = {
        Surface.id
        for Surface in ModelValue.surfaces
        if (isinstance(Surface, TorusSurface) and IsRingTorus(Surface))
        or (isinstance(Surface, SphereSurface) and IsFullSphere(Surface))
    }
    if not Surfaces:
        return frozenset()
    RegionOwners = Counter(Key for Body in ModelValue.bodies for Key in Body.region_ids)
    UseOwners = Counter(
        Key for Region in ModelValue.regions for Key in Region.shell_use_ids
    )
    ShellUses = {Value.id: Value for Value in ModelValue.shell_uses}
    ShellOwners = Counter(Value.shell_id for Value in ModelValue.shell_uses)
    SolidShells = {
        ShellUses[Key].shell_id
        for Region in ModelValue.regions
        if Region.solid and RegionOwners[Region.id] == 1
        for Key in Region.shell_use_ids
        if Key in ShellUses
        and UseOwners[Key] == 1
        and ShellOwners[ShellUses[Key].shell_id] == 1
    }
    FaceUseOwners = Counter(
        Key for Shell in ModelValue.shells for Key in Shell.face_use_ids
    )
    ClosedUses = {
        Shell.face_use_ids[0]
        for Shell in ModelValue.shells
        if Shell.id in SolidShells
        and Shell.closed
        and len(Shell.face_use_ids) == 1
        and FaceUseOwners[Shell.face_use_ids[0]] == 1
    }
    FaceOwners = Counter(Value.face_id for Value in ModelValue.face_uses)
    ClosedFaces = {
        Value.face_id
        for Value in ModelValue.face_uses
        if Value.id in ClosedUses and FaceOwners[Value.face_id] == 1
    }
    return frozenset(
        Face.id
        for Face in ModelValue.faces
        if not Face.loop_ids and Face.surface_id in Surfaces and Face.id in ClosedFaces
    )
