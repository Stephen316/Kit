# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Check full PMI databases against the independently decoded driving dimensions."""

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from struct import unpack_from
from uuid import UUID

from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from PartPmiDatabase import EncodePmiDb, KFirstSketchVisual, KPmiDb, PmiIndex, PmiLength
from VerifyBossOpen import verify_measured
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyObjectExchangeDb import LiveRecords
from VerifyRectDims import measured_lengths
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart


# PMI already has an independent key for each typed dimension and a database clock
def ReadPmiIndex(Source: bytes) -> PmiIndex:
    Records = LiveRecords(Source)
    Names = tuple(UUID(Key.decode("ascii")) for Key, _ in Records)
    (Time,) = unpack_from(">I", Source, 11)
    Created = datetime(
        1980 + (Time >> 25),
        (Time >> 21) & 15,
        (Time >> 16) & 31,
        (Time >> 11) & 31,
        (Time >> 5) & 63,
        (Time & 31) * 2,
    )
    return PmiIndex(Names, Created)


# first saves identify the initial document title while later saves use the local short form
def ReadComponent(Archive: SldprtArchive, Generation: int) -> str | None:
    Header, _ = ReadHeaderLogs(Archive.require("Header2"), Generation)
    Self = ReadHeaderSelf(Header, Generation)
    return None if Self.File.FilePath else Self.File.Title


# combine resolved type ownership with the independently licensed readback
def ReadDimensions(Archive: SldprtArchive, Generation: int, Measurement):
    Part = ReadRectPart(
        Archive.require("Contents/Config-0"),
        Archive.require("Contents/Config-0-ResolvedFeatures"),
        Generation,
    )
    Profile = Part.Profile
    Lengths = measured_lengths(Measurement, Profile.NameValue)
    Sketch = Profile.Geometry["length_dimensions"]
    require(len(Sketch) == 2, "two independently owned sketch distances")
    Dimensions = []
    for Slot, (Driver, Reading) in enumerate(zip(Sketch, Lengths, strict=True)):
        require(
            (Driver["name"], Driver["metres"])
            == (Reading["name"], Reading["system_value"]),
            "independent PMI sketch length",
        )
        Dimensions.append(
            PmiLength(
                Driver["name"],
                Profile.NameValue,
                KFirstSketchVisual + Slot,
                Driver["metres"],
                False,
            )
        )
    require(
        (Part.Boss is not None) == bool(Measurement["body_count"]),
        "ordinary PMI Boss roster",
    )
    if Part.Boss is not None:
        verify_measured(Part.Boss, Measurement)
        Depth = Part.Boss["depth_display"]["dimension"]
        Dimensions.append(
            PmiLength(
                Depth["parameter_name"],
                Part.Boss["name"],
                0,
                abs(Depth["metres"]),
                True,
            )
        )
    return tuple(Dimensions)


# reconstruct complete member contents across the original and changed geometry
def Report():
    Cases = {}
    Counts = Counter()
    FullCount = 0
    AnnotationCount = 0
    for Recipe, Asset, Raw, _, Measurement in principal_captures():
        Archive = SldprtArchive.from_bytes(Raw, Asset["path"])
        Generation = ContainerMo(Archive.streams)
        Source = Archive.require(KPmiDb)
        Index = ReadPmiIndex(Source)
        Component = ReadComponent(Archive, Generation)
        Dimensions = ReadDimensions(Archive, Generation, Measurement)
        Fresh = EncodePmiDb(Generation, Index, Component, Dimensions)
        require(Fresh == Source, f"complete PMI database differs: {Asset['sha256']}")
        Counts[Recipe] += 1
        FullCount += Component is not None
        AnnotationCount += len(Dimensions)
        Cases[Asset["sha256"]] = sha256(Fresh).hexdigest()
    require(Counts == {"P01": 6, "P03": 8}, "ordinary PMI discovery scope")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "full_presentation": FullCount,
        "annotations": AnnotationCount,
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(Report(), sort_keys=True))
