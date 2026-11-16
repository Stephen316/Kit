from hashlib import sha256
from struct import calcsize

from Display.Compose import DisplayDraft, KDisplayClass
from DisplayBaseHead import KBaseHeadFormat
from DisplayCache import KAuthoredMask, KLoadFixupMask
from DisplayFavorite import KFavoriteClass
from DisplayMasks import DisplayPrefs
from OriginSketch import KObjectList
from RectDimDisplay import KSketchCacheBit, KSketchHandle, WriteRectDisplays
from RectDisplayPose import DisplayRefPoint, DisplayTextDirection, SketchDisplayPose
from RectangleDims import KDistanceClass, RectangleLength
from VerifyConfigRoot import require
from VerifyRectDims import measured_lengths
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimHandle
from convert.adapters.solidworks.Sketch.DisplayFields import (
    ReadCache,
    ReadDisplayTail,
    ReadEmptyTexts,
)
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayOpen
from convert.adapters.solidworks.Sketch.Displays import ReadDisplays, TakeShownClass
from convert.adapters.solidworks.Sketch.Regions import ReadRegionStart

DRAFT = DisplayDraft(
    Preferences=DisplayPrefs(
        design_intent=True,
        inward_tolerance_rounding=False,
        remove_zero=False,
        uppercase_dimension=False,
    ),
    Alignment=(1, 1),
    Standard=4,
    ExtendLeader=True,
    SplitDual=False,
    ArrowHead=0,
    Precision=2,
    AltPrecision=2,
)


# the collection's loaded cache flag is independent of the current native system length
def saved_mask(cursor):
    fields = FieldCursor(cursor.BlobValue, cursor.Offset + calcsize("<2H"))
    fields.ReadValue("<2d2i2H")
    (mask,) = fields.ReadInts("<I")
    require(
        mask & ~KLoadFixupMask == KAuthoredMask | KSketchCacheBit,
        "ordinary sketch cache fields",
    )
    return bool(mask & KLoadFixupMask)


# the only byte normalization follows the known ignored and inactive owners
def saved_close(cursor):
    start = cursor.Offset
    ReadDisplayTail(cursor)
    head = FieldCursor(cursor.BlobValue, start)
    head.ReadInts("<2iI")
    head.ReadValue(KBaseHeadFormat)
    head.ReadPoint(9)
    require(head.ReadInts("<I") == (1,), "ordinary foreshortening state")
    padding = head.Offset
    return_width = calcsize("<i5diHi")
    end_width = calcsize("<3d2iI")
    fields = FieldCursor(
        cursor.BlobValue, cursor.Offset - return_width - end_width - calcsize("<2i")
    )
    side_offset = fields.Offset + calcsize("<i")
    set_point, side = fields.ReadInts("<2i")
    require(
        set_point == 0 and fields.ReadPoint(3) == (0.0, 0.0, 0.0),
        "inactive display shifted point",
    )
    require(side in (0, 3407917, 6029357), "witnessed inactive side values")
    return padding, side_offset


# the original native authoring point was selected before any width or height edit
def expected_point(measured, slot):
    frame = measured["model_to_sketch_transform"]
    normal = (frame[2], frame[5], frame[8])
    require(
        normal in ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)), "ordinary licensed sketch plane"
    )
    return tuple(0.0001 * slot if axis else 0.075 for axis in normal)


# inspect real scalar and map boundaries, including the sketch alias and dimension slot
def read_display(cursor, profile, slot, corners, length, measured):
    TakeShownClass(cursor, KDisplayClass)
    ReadDisplayOpen(cursor, True)
    text = FieldCursor(
        cursor.BlobValue, cursor.Offset - calcsize("<3diHi4d4i2diH3id2i")
    )
    position = text.ReadPoint(3)
    require(
        position == expected_point(measured, slot),
        "authored world anchor and normal lift",
    )
    TakeShownClass(cursor, KSketchHandle)
    require(
        ReadDimHandle(cursor, profile.SketchIndex) == slot,
        "display owns the actual dimension slot",
    )
    require(cursor.ReadInts("<3H") == (0, 0, 0), "ordinary display arrows")
    ReadEmptyTexts(cursor, 4)
    fields = cursor.ReadPoint(22)
    require(
        cursor.ReadInts("<i7H") == (0, 0, 0, 0, 4, 2, 2, 2),
        "ordinary sketch witness settings",
    )
    direction = cursor.ReadPoint(3)
    pose = SketchDisplayPose(position, fields[3], fields[4], direction)
    require(
        pose.TextRatio == 0.075 / (0.04, 0.02)[slot] and pose.WitnessMetres == 0.075,
        "saved annotation keeps baseline authoring placement",
    )
    point = DisplayRefPoint(corners, length, pose)
    require(
        fields[:3] == DisplayTextDirection(direction, slot),
        "text direction in the actual local frame",
    )
    require(fields[13:19] == (*point, *point), "paired dimension witness points")
    restored = saved_mask(cursor)
    require(
        ReadCache(cursor) == (length.Millimetres / 1000.0,) * 2,
        "display copies retain the owned length",
    )
    TakeShownClass(cursor, KFavoriteClass)
    padding, inactive = saved_close(cursor)
    return pose, restored, (padding, inactive)


# check the actual display-list return and use the live writer when CI requests construction
def verify_display_list(cursor, profile, corners, measurement, generation, writer):
    start = cursor.Offset
    before = map_state(cursor)
    normal = before.Cursor(cursor.BlobValue, start)
    ReadDisplays(normal, profile.Geometry)
    (sketch,) = [
        row for row in measurement["sketches"] if row["name"] == profile.NameValue
    ]
    measured = measured_lengths(measurement, profile.NameValue)
    lengths = tuple(
        RectangleLength(row["name"], native["native_id"], row["system_value"] * 1000.0)
        for row, native in zip(
            measured, profile.Geometry["length_dimensions"], strict=True
        )
    )
    TakeShownClass(cursor, KObjectList)
    require(
        cursor.ReadInts("<H") == (len(lengths),), "two independent dimension displays"
    )
    records = [
        read_display(cursor, profile, slot, corners, length, sketch)
        for slot, length in enumerate(lengths)
    ]
    after = map_state(cursor)
    end = cursor.Offset
    require(
        (end, after) == (normal.Offset, map_state(normal)),
        "same normal display return and complete map",
    )
    require(
        after.NextIndex == before.NextIndex + 10,
        "three new classes and seven new objects",
    )
    ReadRegionStart(normal)
    raw = cursor.BlobValue[start:end]
    restored = {record[1] for record in records}
    require(len(restored) == 1, "both displays share the saved reference history")
    (restored_mode,) = restored
    poses = tuple(record[0] for record in records)
    inactive = tuple(offset for _, _, words in records for offset in words)
    if writer is not None:
        require(
            writer.Snapshot() == before,
            "display writer receives the live sketch namespace",
        )
        owned = tuple(
            index
            for index, name in before.Objects
            if index > profile.SketchIndex and name == KDistanceClass
        )
        position = len(writer.build())
        WriteRectDisplays(
            writer,
            generation,
            profile.SketchIndex,
            owned,
            corners,
            lengths,
            poses,
            DRAFT,
            Restored=restored_mode,
        )
        comparison = bytearray(raw)
        for offset in inactive:
            comparison[offset - start : offset - start + 4] = bytes(4)
        require(
            writer.build()[position:] == comparison,
            "exact display bytes with known inactive fields normalized",
        )
        require(
            writer.Snapshot() == after, "constructed display and favorite allocations"
        )
    proof = (start, end, before.NextIndex, after.NextIndex, sha256(raw).hexdigest())
    return proof, poses, restored_mode, inactive
