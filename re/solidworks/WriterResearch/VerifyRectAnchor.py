from hashlib import sha256

from OriginSketch import KObjectList
from RectangleAnchor import WriteRectAnchor
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.SketchTail import ReadLogicalTail


# independently observed operand IDs distinguish the proxy from the coincident corner
def measured_anchor(measurement, name):
    (sketch,) = [row for row in measurement["sketches"] if row["name"] == name]
    (relation,) = [row for row in sketch["relations"] if row["type"] == 9]
    require(relation["entity_types"] == [2, 2], "two licensed coincidence points")
    require(
        all(row["point_local_mm"] == [0, 0, 0] for row in relation["entities"]),
        "both points measured at the local Origin",
    )
    return [tuple(row["id"]) for row in relation["entities"]]


# replay the complete logical return and stop at the inherited display list class
def verify_anchor(cursor, profile, points, measurement, generation, writer):
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    point_ids = [point["id"] for point in profile.Geometry["point_relation_tallies"]]
    (anchor,) = ReadLogicalTail(sketch, point_ids)
    require(profile.Coincidences == [anchor], "exact native coincidence owner and span")
    require(
        anchor["point_native_ids"] == measured_anchor(measurement, profile.NameValue),
        "ordered licensed coincidence operands",
    )
    require(
        not anchor["deleted"] and not anchor["suppressed"],
        "active anchored coincidence",
    )
    end = sketch.Offset
    after = map_state(sketch)
    require(
        after.NextIndex == before.NextIndex + 2, "two new coincidence point handles"
    )
    display = after.Cursor(cursor.BlobValue, end)
    display.TakePointer((KObjectList,), KClassRefKind, CompactOnly=True)
    require(
        display.ReadInts("<H") == (2,), "next owner is the two-dimension display list"
    )
    if writer is not None:
        require(
            writer.Snapshot() == before,
            "coincidence writer receives the same enclosing map",
        )
        position = len(writer.build())
        WriteRectAnchor(
            writer,
            generation,
            profile.SketchIndex,
            points,
            tuple(anchor["point_indices"]),
        )
        require(
            writer.build()[position:] == cursor.BlobValue[start:end],
            "exact typed coincidence and logical return",
        )
        require(writer.Snapshot() == after, "constructed logical group map")
    cursor.Offset = end
    cursor.NextIndex = sketch.NextIndex
    return (
        start,
        end,
        before.NextIndex,
        after.NextIndex,
        sha256(cursor.BlobValue[start:end]).hexdigest(),
    )
