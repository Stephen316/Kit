from hashlib import sha256

from RectangleCorners import (
    ContourPairs,
    CornerPoint,
    KCornerMask,
    KLineHandle,
    KMemberStatus,
    WriteRectCorners,
)
from RectangleFields import member_geometry, member_prefix
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Members import ReadPointMut


# allocated child handles must have exactly the same two incident line identities
def verify_handles(cursor, point, expected, first):
    cursor.PointerEvents = []
    result = ReadPointMut(cursor)
    require(
        result == (point.Identity, point.RelationCount, point.Position),
        "typed corner agrees with licensed graph",
    )
    handles = [
        (kind, cursor.Handles[index])
        for _, _, kind, name, index in cursor.PointerEvents
        if name == KLineHandle
    ]
    require(
        handles
        == [
            (
                KDefinitionKind if first and ordinal == 0 else KClassRefKind,
                (line, -1, 0),
            )
            for ordinal, line in enumerate(expected)
        ],
        "two new contour handles from the saved local graph",
    )


# preserve the archive snapshot before the external Origin point begins allocating
def verify_corners(cursor, profile, corners, endpoints, tallies, generation, writer):
    stream = cursor.BlobValue
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    points = tuple(
        CornerPoint(slot + 1, point, tallies[2, slot, slot + 1])
        for slot, point in enumerate(corners)
    )
    masks = set()
    statuses = set()
    for slot, (point, handles) in enumerate(
        zip(points, ContourPairs(points, endpoints), strict=True)
    ):
        span = profile.Members.Points[slot]
        require(sketch.Offset == span.Offset, "corner start from the sketch owner")
        prefix = member_prefix(stream, span)
        geom, _, _ = member_geometry(stream, prefix)
        mask = int.from_bytes(stream[geom : geom + 2], "little")
        status_start = prefix["tally"] + 8
        status = int.from_bytes(stream[status_start : status_start + 2], "little")
        masks.add(mask)
        statuses.add(status)
        verify_handles(sketch, point, handles, slot == 0)
        require(sketch.Offset == span.EndOffset, "corner return from the sketch owner")
    require(
        (masks, statuses) == ({KCornerMask}, {KMemberStatus}),
        "witnessed corner mask and status",
    )
    end = sketch.Offset
    require(end == profile.Members.Points[-1].Offset, "next member is the Origin proxy")
    require(
        sketch.NextIndex == before.NextIndex + 9, "one class and eight corner handles"
    )
    if writer is not None:
        require(writer.Snapshot() == before, "generated sketch before corners")
        WriteRectCorners(
            writer,
            generation,
            profile.SketchIndex,
            points,
            endpoints,
            Mask=next(iter(masks)),
            Status=next(iter(statuses)),
        )
        require(writer.build() == stream[:end], "exact framed ordinary corner bytes")
        require(
            writer.Snapshot() == map_state(sketch), "exact ordinary corner archive map"
        )
    cursor.Offset = end
    cursor.NextIndex = sketch.NextIndex
    return (
        start,
        end,
        before.NextIndex,
        sketch.NextIndex,
        sha256(stream[start:end]).hexdigest(),
    )
