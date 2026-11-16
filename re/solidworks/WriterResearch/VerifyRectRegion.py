from hashlib import sha256
from math import isclose

from RectangleRegion import CheckRectOutline, SketchRegionState, WriteRectRegion
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Regions import ReadRegion, ReadRegionStart


# the inherited presentation grammar locates the update serial before the nested region list
def read_serial(blob, offset):
    fields = FieldCursor(blob, offset)
    require(
        fields.ReadInts("<7H2Hi") == (0, 0, 0, 0, 0, 0, 0, 2, 1, 5),
        "ordinary sketch presentation state",
    )
    fields.ReadInts("<15i4H")
    require(fields.ReadText() == "", "no additional sketch line style")
    fields.ReadValue("<Hf3i3d")
    (serial,) = fields.ReadInts("<I")
    return serial


# measured section area and the current sketch graph corroborate the region enclosure
def verify_section(measurement, profile, corners):
    (measured,) = [
        row for row in measurement["sketches"] if row["name"] == profile.NameValue
    ]
    require(measured["region_count"] == 1, "one independently measured sketch region")
    xs, ys = zip(*corners, strict=True)
    area = (max(xs) - min(xs)) * (max(ys) - min(ys)) * 1e6
    require(
        isclose(measured["section_area_mm2"], area, abs_tol=1e-8, rel_tol=0),
        "licensed local contour area",
    )


# region handles are local line identities and the next byte belongs to the outer profile
def verify_region(
    cursor, normal, profile, edges, corners, measurement, generation, writer
):
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    ReadRegionStart(sketch)
    region_start = sketch.Offset
    serial = read_serial(cursor.BlobValue, start)
    ReadRegion(sketch, profile.Geometry["lines"])
    region_end = sketch.Offset
    outline = tuple(fields[0] for fields in sketch.Handles.values())
    CheckRectOutline(edges, outline)
    verify_section(measurement, profile, corners)
    require(sketch.ReadInts("<H7i") == (0,) * 8, "empty post-region sketch records")
    end = sketch.Offset
    after = map_state(sketch)
    require(
        (end, after) == (normal.Offset, map_state(normal)),
        "same complete inline sketch return",
    )
    require(
        after.NextIndex == before.NextIndex + 8, "one region class and seven objects"
    )
    raw = cursor.BlobValue[start:end]
    region = SketchRegionState(serial, outline)
    if writer is not None:
        require(
            writer.Snapshot() == before,
            "region writer receives the live sketch namespace",
        )
        position = len(writer.build())
        WriteRectRegion(
            writer,
            generation,
            profile.SketchIndex,
            edges,
            region,
        )
        require(
            writer.build()[position:] == raw,
            "exact sketch environment, region and return",
        )
        require(writer.Snapshot() == after, "exact region list and outline allocations")
    cursor.Offset = end
    cursor.NextIndex = sketch.NextIndex
    proof = (
        start,
        region_start,
        region_end,
        end,
        before.NextIndex,
        after.NextIndex,
        serial,
        sha256(raw).hexdigest(),
    )
    return proof, region
