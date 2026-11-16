from hashlib import sha256

from RectangleDims import (
    KDistanceClass,
    KDrivingNames,
    RectangleLength,
    RectLengthSlots,
    WriteRectDims,
)
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Relations import ReadDims


# the measured owner and driving role travel with the unrounded native system value
def measured_lengths(measurement, name):
    (feature,) = [row for row in measurement["feature_tree"] if row["name"] == name]
    rows = feature["dimensions"]
    require(
        tuple(row["name"] for row in rows) == KDrivingNames,
        "independent width and height roles",
    )
    require(
        all(
            row["driven_state"] == 2 and row["full_name"].split("@")[1] == name
            for row in rows
        ),
        "measurement is driving and owned by this sketch",
    )
    return rows


# the owned value group must reproduce both independent operands and its exact return map
def verify_dims(cursor, profile, corners, measurement, generation, writer):
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    sketch.PointerEvents = []
    ReadDims(sketch)
    require(
        tuple(span for _, span in sketch.Dimensions) == profile.Members.Distances,
        "typed distance body boundaries",
    )
    measured = measured_lengths(measurement, profile.NameValue)
    lengths = []
    for (saved, state), row in zip(sketch.Dimensions, measured, strict=True):
        class_name, identity, label, value, first, second = saved
        require(
            (class_name, label, value)
            == (KDistanceClass, row["name"], row["system_value"]),
            "owned unrounded sketch length",
        )
        require(state.ActivePair and state.TypeCode == 1, "active two-point distance")
        slots = RectLengthSlots(corners, row["system_value"])
        require(
            (sketch.Handles[first], sketch.Handles[second])
            == tuple((slot, -1, 0) for slot in slots),
            "measurement-selected local point pair",
        )
        lengths.append(RectangleLength(label, identity, row["system_value"] * 1000.0))
    allocated = tuple(
        index for _, _, _, name, index in sketch.PointerEvents if name == KDistanceClass
    )
    after = map_state(sketch)
    require(
        after.NextIndex == before.NextIndex + 12 and len(allocated) == 2,
        "two independent distance and length allocations",
    )
    end = sketch.Offset
    if writer is not None:
        generated = WriteRectDims(
            writer, generation, profile.SketchIndex, corners, tuple(lengths)
        )
        require(generated == allocated, "exact generated distance object IDs")
        require(
            writer.build() == cursor.BlobValue[:end],
            "exact framed pre-dimension counts and distances",
        )
        require(
            writer.Snapshot() == after,
            "constructed dimensions preserve all archive allocations",
        )
    cursor.Offset = end
    cursor.NextIndex = sketch.NextIndex
    return (
        start,
        end,
        before.NextIndex,
        after.NextIndex,
        sha256(cursor.BlobValue[start:end]).hexdigest(),
    )
