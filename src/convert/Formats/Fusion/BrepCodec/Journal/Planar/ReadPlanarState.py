from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell


# the planar state operation needs a distinct decoding boundary so topology changes retain their native revision relationships
def ReadPlanarState(
    Model: JournalModel, StateId: int | None = None
) -> tuple[PlanarShell, ...]:
    Table = MakeLiveTable(Model, StateId)
    Bodies = tuple(
        Reference
        for Reference in Table.LiveSlots
        if isinstance(Table.Entities[Reference], BodyNode)
    )
    return tuple(ReadPlacedBody(Table, Reference) for Reference in Bodies)
