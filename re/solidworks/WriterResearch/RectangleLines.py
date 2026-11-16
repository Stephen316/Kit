from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from AuthoredProfile import KSketchClass
from OriginProxy import KPointBackup
from PartArchive import PartArchiveWriter
from SketchMember import WriteMemberEnd, WriteMemberOpen
from SketchMemberStyle import COLOR_STATUS_TYPE, Weight, initial_display_state
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KDeletedSlots = (0, 1)
KCreationIds = (1, 2, 3, 4)
KPermMarkOrders = ((1, 2, 3, 4), (1, 4, 3, 2))


# permanent marks belong to the saved model, while endpoints follow their point slots
@Dataclass(frozen=True, slots=True)
class RectangleLine:
    PermMark: int
    CreationId: int
    Endpoints: tuple[int, int]
    RelationCount: int


# a deleted line keeps its array slot while contour membership belongs to live edges
def WriteLine(Writer: PartArchiveWriter, Line: RectangleLine, Deleted: bool) -> None:
    Display = initial_display_state() if Deleted else COLOR_STATUS_TYPE.pack(4, 2, 1)
    Width = Weight.THIN if Deleted else Weight.NORMAL
    WriteMemberOpen(
        Writer, 0, Line.PermMark, Line.CreationId, Line.RelationCount, Display, Width
    )
    Writer.raw(EncodeNull())
    WriteMemberEnd(Writer, 5 if Deleted else 4)
    Writer.raw(PackFields("<4HdH", *Line.Endpoints, int(not Deleted), 0, -1.0, 0))


# emit the deleted slot and the four directed perimeter members without new pointers
def WriteRectLines(
    Writer: PartArchiveWriter,
    Generation: int,
    Sketch: int,
    Lines: tuple[RectangleLine, ...],
) -> None:
    RequireArch(Generation, 19000, "ordinary rectangle line generation")
    RequireArch(
        Writer.objects.get(Sketch) == KSketchClass
        and Writer.next_index == Sketch + 20
        and Writer.objects.get(Writer.next_index - 1) == KPointBackup,
        True,
        "line array follows owned points and their proxy",
    )
    RequireArch(
        tuple(Line.CreationId for Line in Lines),
        KCreationIds,
        "ordered rectangle line identities",
    )
    RequireArch(
        tuple(Line.PermMark for Line in Lines) in KPermMarkOrders,
        True,
        "witnessed permanent marks",
    )
    RequireArch(
        tuple(len(Line.Endpoints) for Line in Lines),
        (2, 2, 2, 2),
        "two local slots per perimeter line",
    )
    RequireArch(
        all(
            Line.RelationCount == 1
            and Line.Endpoints[0] != Line.Endpoints[1]
            and all(type(Slot) is int and 0 <= Slot < 4 for Slot in Line.Endpoints)
            for Line in Lines
        ),
        True,
        "local four-edge contour and axis incidences",
    )
    Edges = {frozenset(Line.Endpoints) for Line in Lines}
    RequireArch(
        len(Edges) == 4
        and all(sum(Slot in Edge for Edge in Edges) == 2 for Slot in range(4)),
        True,
        "one closed rectangle contour",
    )
    Writer.i32(len(Lines) + 1)
    WriteLine(Writer, RectangleLine(0, -1, KDeletedSlots, 0), True)
    for Line in Lines:
        WriteLine(Writer, Line, False)
