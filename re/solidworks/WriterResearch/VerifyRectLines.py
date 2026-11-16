from hashlib import sha256

from RectangleLines import KDeletedSlots, KPermMarkOrders, RectangleLine, WriteRectLines
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Members import ReadLineItem


# the production line reader corroborates the separate deleted record and stable authored identities
def verify_lines(cursor, profile, endpoints, tallies, generation, writer):
    stream = cursor.BlobValue
    start = cursor.Offset
    before = map_state(cursor)
    sketch = SketchArchive(cursor)
    count = sketch.ReadCount()
    require(
        count == len(endpoints) + 1 == len(profile.Members.Lines),
        "one deleted slot and four authored lines",
    )
    lines = []
    for slot, span in enumerate(profile.Members.Lines):
        require(sketch.Offset == span.Offset, "line bound to its owning profile")
        mark, creation, flags, first, second = ReadLineItem(
            sketch, len(profile.Members.Points)
        )
        require(
            sketch.Offset == span.EndOffset, "line record returns at its typed boundary"
        )
        if slot == 0:
            require(
                (mark, creation, flags, (first, second)) == (0, -1, 5, KDeletedSlots),
                "structural deleted slot",
            )
            continue
        require(
            (creation, flags, (first, second)) == (slot, 4, endpoints[creation]),
            "directed measured perimeter",
        )
        lines.append(
            RectangleLine(
                mark, creation, endpoints[creation], tallies[3, creation, creation]
            )
        )
    after = map_state(sketch)
    require(
        after == before,
        "inline line records leave all archive allocation maps unchanged",
    )
    marks = tuple(line.PermMark for line in lines)
    require(marks in KPermMarkOrders, "witnessed mark assignment")
    end = sketch.Offset
    if writer is not None:
        WriteRectLines(writer, generation, profile.SketchIndex, tuple(lines))
        require(writer.build() == stream[:end], "exact framed line count and members")
        require(
            writer.Snapshot() == after, "line writer retains the shared archive map"
        )
    cursor.Offset = end
    return start, end, before.NextIndex, marks, sha256(stream[start:end]).hexdigest()
