from dataclasses import dataclass

from typing_extensions import override as Override

from convert.adapters.solidworks.Container.Archive import KBigObjectTag, EncodeObjectRef
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import (
    ArchiveWriter,
    KFirstLoadArrayIndex,
)


@dataclass(frozen=True, slots=True)
class PartArchiveState:
    NextIndex: int
    Classes: tuple[tuple[int, str], ...]
    Objects: tuple[tuple[int, str], ...]

    def __post_init__(self) -> None:
        RequireArch(
            type(self.Classes) is tuple
            and type(self.Objects) is tuple
            and all(type(Entry) is tuple for Entry in (*self.Classes, *self.Objects)),
            True,
            "immutable archive slot entries",
        )
        RequireArch(
            type(self.NextIndex) is int
            and KFirstLoadArrayIndex <= self.NextIndex <= KBigObjectTag,
            True,
            "compact generated archive counter",
        )
        Slots = (*self.Classes, *self.Objects)
        RequireArch(
            len({Index for Index, _ in Slots}) == len(Slots)
            and all(
                type(Index) is int and issubclass(type(Name), str) and Name
                for Index, Name in Slots
            )
            and {Index for Index, _ in Slots}
            == set(range(KFirstLoadArrayIndex, self.NextIndex)),
            True,
            "every generated archive slot has exactly one owner",
        )
        RequireArch(
            len({Name for _, Name in self.Classes}),
            len(self.Classes),
            "unique archive class names",
        )

    def Cursor(self, BlobValue: bytes, Offset: int) -> ArchiveCursor:
        return ArchiveCursor(
            BlobValue, Offset, self.NextIndex, dict(self.Classes), dict(self.Objects)
        )


# Keep native object ownership alongside the existing name-to-class-slot writer.
class PartArchiveWriter(ArchiveWriter):
    def __init__(self, State: PartArchiveState | None = None) -> None:
        super().__init__()
        self.objects: dict[int, str] = {}
        if State is not None:
            self.SetNextIndex(State.NextIndex)
            self.classes.update((Name, Index) for Index, Name in State.Classes)
            self.objects.update(State.Objects)

    @Override
    def BeginObject(self, NameValue: str, Schema: int) -> None:
        RequireArch(
            issubclass(type(NameValue), str) and bool(NameValue),
            True,
            "nonempty archive class name",
        )
        ObjectIndex = self.next_index + int(NameValue not in self.classes)
        RequireArch(
            0 < self.next_index <= ObjectIndex < KBigObjectTag
            and all(
                Slot not in self.objects and Slot not in self.classes.values()
                for Slot in range(self.next_index, ObjectIndex + 1)
            ),
            True,
            "compact generated object allocation",
        )
        super().BeginObject(NameValue, Schema)
        self.objects[ObjectIndex] = NameValue

    begin_object = BeginObject

    # Native direct map insertions consume an index without writing a pointer tag.
    def ReserveObject(self, NameValue: str) -> int:
        ObjectIndex = self.next_index
        RequireArch(
            issubclass(type(NameValue), str)
            and bool(NameValue)
            and 0 < ObjectIndex < KBigObjectTag
            and ObjectIndex not in self.objects
            and ObjectIndex not in self.classes.values(),
            True,
            "implicit compact archive object",
        )
        self.objects[ObjectIndex] = NameValue
        self.SetNextIndex(ObjectIndex + 1)
        return ObjectIndex

    # An alias occupies a stream entry but reuses the established object index.
    def ReferenceObject(self, Index: int, NameValue: str) -> None:
        RequireArch(type(Index) is int, True, "integer archive object alias index")
        RequireArch(
            self.objects.get(Index), NameValue, "allocated archive object alias"
        )
        self.raw(EncodeObjectRef(Index))

    def Snapshot(self) -> PartArchiveState:
        return PartArchiveState(
            self.next_index,
            tuple(sorted((Index, Name) for Name, Index in self.classes.items())),
            tuple(sorted(self.objects.items())),
        )
