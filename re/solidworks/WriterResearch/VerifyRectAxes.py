from hashlib import sha256

from RectangleAxes import RectAxisType, WriteRectAxes
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Relations import ReadRelations


# each independent native relation is a local line identity and sketch-axis type
def measured_axes(measurement, profile):
    (sketch,) = [
        row for row in measurement["sketches"] if row["name"] == profile.NameValue
    ]
    rows = []
    for relation in sketch["relations"]:
        if relation["type"] in (4, 5):
            require(relation["entity_types"] == [3], "one measured axis line")
            (entity,) = relation["entities"]
            first, second = entity["id"]
            require(
                first == second and entity["segment_type"] == 0,
                "measured stable local line identity",
            )
            rows.append((first, relation["type"]))
    require(
        len(rows) == len({row[0] for row in rows}) == 4,
        "one measured constraint per perimeter line",
    )
    return rows


# typed replay joins the saved handle to the observed axis and line topology
def verify_axes(cursor, profile, corners, edges, measurement, generation, writer):
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    relations = ReadRelations(sketch)
    require(
        len(relations) == len(profile.Geometry["member_relations"]) == 4,
        "ordinary axis relation count",
    )
    measured = measured_axes(measurement, profile)
    order = []
    for relation, archived, native in zip(
        relations, profile.Geometry["member_relations"], measured, strict=True
    ):
        first, end, target, kind, flags = relation
        identity, code = native
        require(
            (first, end) == (archived["start"], archived["end"]), "same typed axis span"
        )
        require(
            kind == code == RectAxisType(corners, edges[identity]),
            "native axis matches local geometry",
        )
        require(
            sketch.Handles[target] == (identity, -1, 0) and flags == (65534, 0),
            "bound line handle and ordinary axis state",
        )
        order.append(identity)
    end = sketch.Offset
    after = map_state(sketch)
    require(
        (end, after.NextIndex)
        == (profile.Geometry["geometry_end"], before.NextIndex + 4),
        "axis return and new handles",
    )
    if writer is not None:
        WriteRectAxes(
            writer, generation, profile.SketchIndex, corners, edges, tuple(order)
        )
        require(
            writer.build() == cursor.BlobValue[:end],
            "exact framed axis records",
        )
        require(writer.Snapshot() == after, "constructed axis handle allocations")
    cursor.Offset = end
    cursor.NextIndex = sketch.NextIndex
    return (
        start,
        end,
        before.NextIndex,
        after.NextIndex,
        sha256(cursor.BlobValue[start:end]).hexdigest(),
    )
