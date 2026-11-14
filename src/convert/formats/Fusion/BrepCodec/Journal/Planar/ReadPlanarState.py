from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell


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
