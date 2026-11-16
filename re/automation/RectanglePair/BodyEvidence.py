# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math as MathValue

from PairedCaptureIntake import require
from RectanglePairSketch import same, xyz


# the independently measured sketch cases must remain free of phantom bodies
def CheckNoBodies(Document, Measured):
    Count = Measured["body_count"]
    require(
        type(Count) is int and Count == len(Document.bodies) == 0,
        "public sketch body roster differs from its recorded native observation",
    )
    return {"public_count": len(Document.bodies), "native_count": Count}


# a matching roster cannot conceal which feature owns the actual result solid
def CheckBossBody(Document, Measured, OwnerId):
    Count = Measured["body_count"]
    require(
        type(Count) is int and Count == len(Document.bodies) == 1,
        "public boss body roster differs from its recorded native observation",
    )
    (BodyValue,) = Document.bodies
    require(
        BodyValue.topology.solid_count == 1 and BodyValue.final_feature_id == OwnerId,
        "public body does not identify the verified boss as its final owner",
    )
    return BodyValue, {
        "public_count": len(Document.bodies),
        "native_count": Count,
        "body_id": BodyValue.id,
        "final_feature_id": BodyValue.final_feature_id,
    }


# preserve absent neutral volume separately from the independently measured volume
def CompareVolume(Public, Native, Tolerances):
    if Public is not None:
        require(
            MathValue.isclose(
                Public,
                Native,
                abs_tol=Tolerances["volume_mm3_absolute"],
                rel_tol=Tolerances["volume_relative"],
            ),
            "public body volume differs from its recorded native observation",
        )
    return {
        "status": "unavailable" if Public is None else "equal",
        "public_mm3": Public,
        "native_mm3": Native,
    }


# a known native centroid cannot supply a measurement omitted by the public reader
def CompareCenter(Public, Native, Tolerance):
    if Public is not None:
        same(
            Public,
            Native,
            Tolerance,
            "public body centroid differs from its recorded native observation",
        )
    return {
        "status": "unavailable" if Public is None else "equal",
        "public_mm": Public,
        "native_mm": Native,
    }


# preserve the independent fusion bounds and each public reader comparison
def CompareBounds(BodyValue, Native, Tolerance):
    Bounds = BodyValue.topology.bounding_box
    require(Bounds is not None, "public body has no world bounds")
    Public = (xyz(Bounds.minimum), xyz(Bounds.maximum))
    for Actual, Measured in zip(Public, Native, strict=True):
        same(
            Actual,
            Measured,
            Tolerance,
            "public body bounds differ from the native Fusion measurement",
        )
    return Public


# the archived pair separates verified body properties from missing reader data
def CompareBodies(Documents, Observations, Bosses, Tolerances):
    (NativeFusion,) = Observations["fusion"]["bodies"]
    require(NativeFusion["solid"] is True, "native Fusion body is not a measured solid")
    NativeBounds = NativeFusion["bounding_box_mm"]
    Tolerance = Tolerances["length_mm_absolute"]
    Sides = {}
    for Application, Document in Documents.items():
        Measured = Observations[Application]
        BodyValue, Roster = CheckBossBody(
            Document, Measured, Bosses[Application]["step_id"]
        )
        Sides[Application] = {
            **Roster,
            "bounds_mm": CompareBounds(BodyValue, NativeBounds, Tolerance),
            "volume": CompareVolume(
                BodyValue.topology.volume, Measured["volume_mm3"], Tolerances
            ),
            "center_of_mass": CompareCenter(
                BodyValue.attributes.get(f"{Application}.body_centroid_mm"),
                Measured["center_of_mass_mm"],
                Tolerance,
            ),
        }
    return {
        "roster_status": "equal",
        "bounds_status": "equal",
        "native_fusion_bounds_mm": NativeBounds,
        **Sides,
    }
