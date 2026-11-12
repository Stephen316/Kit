from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import (
    KMaxIndexRows,
    KMaxWireId,
)
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord


# native continuations can precede their owners in physical stream order
class BulkOwners:
    __slots__ = ("Primary", "Continues", "OtherCount")

    # separate tracking allows either native index table to be bounded independently
    def __init__(self) -> None:
        super().__init__()
        self.Primary: dict[int, int] = {}
        self.Continues: set[tuple[int, int]] = set()
        self.OtherCount = 0

    # metadata needs distinct owners and a representable next native identity
    def AddRecord(self, RecordValue: BulkRecord) -> None:
        Identity = RecordValue.ObjectId
        if Identity == KMaxWireId:
            raise ValueError("Fusion BulkStream leaves no next object identity")
        if RecordValue.IsPrimary:
            if Identity in self.Primary:
                raise ValueError("Duplicate primary Fusion BulkStream identity")
            if len(self.Primary) >= KMaxIndexRows:
                raise ValueError("Fusion BulkStream primary count exceeds index limit")
            self.Primary[Identity] = RecordValue.TypeCode
        else:
            if self.OtherCount >= KMaxIndexRows:
                raise ValueError(
                    "Fusion BulkStream continuation count exceeds index limit"
                )
            self.OtherCount += 1
            self.Continues.add((Identity, RecordValue.TypeCode))

    # incomplete ownership cannot become a readable pair of native streams
    def CheckComplete(self) -> None:
        if not self.Primary:
            raise ValueError("Fusion BulkStream requires at least one primary record")
        for Identity, TypeCode in self.Continues:
            if Identity not in self.Primary:
                raise ValueError("Fusion BulkStream continuation has no primary owner")
            if self.Primary[Identity] == TypeCode:
                raise ValueError(
                    "Fusion BulkStream continuation repeats its primary class"
                )
