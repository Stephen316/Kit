from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.sketch.GeometryTypes import (
    KDistanceRow,
    KEntityHandle,
    SketchReference,
)
from convert.adapters.solidworks.sketch.Objects import ReadSketchMut


# sketch local operand data shares its ownership map with the enclosing feature
class SketchArchive(ArchiveCursor):

    # local handles need an independent state while their allocations stay with the owner
    def __init__(self, Parent: ArchiveCursor) -> None:
        super().__init__(
            Parent.BlobValue,
            Parent.Offset,
            Parent.NextIndex,
            Parent.Classes,
            Parent.Objects,
        )
        self.PointerEvents = Parent.PointerEvents
        self.NodeNames: dict[int, str] = {}
        self.Scalars: dict[int, tuple[str, float]] = {}
        self.ScalarOffsets: dict[int, int] = {}
        self.Dimensions: list[KDistanceRow] = []
        self.Handles: dict[int, KEntityHandle] = {}
        self.SketchReferences: dict[int, SketchReference] = {}
        self.PointReferences: dict[int, SketchReference] = {}

    # new local objects must consume their own fields before later aliases can resolve
    def ReadObject(self, *Expected: str | None) -> int:
        TagValue, NameValue, ObjectIndex = self.TakePointer(Expected)
        if NameValue is not None and TagValue.kind in (KDefinitionKind, KClassRefKind):
            self.ReadPayload(NameValue, ObjectIndex)
        return ObjectIndex

    # layouts outside the normal sketch scope must fail at their typed boundary
    def ReadPayload(self, NameValue: str, ObjectIndex: int) -> None:
        ReadSketchMut(self, NameValue, ObjectIndex)
