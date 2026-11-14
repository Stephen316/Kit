from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable


def StableRef(Table: LiveTable, Reference: int) -> int:
    if not 0 <= Reference < len(Table.SlotMap):
        raise ValueError("Missing Fusion planar ownership reference")
    return Table.SlotMap[Reference]
