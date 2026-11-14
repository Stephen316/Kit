from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def CheckRoots(Records: tuple[EntityRecord, ...]) -> None:
    Names = tuple(
        Record.Frame.RootId
        for Record in Records
        if Record.IsPrimary and Record.Frame.RootId
    )
    if len(set(Names)) != len(Names):
        raise ValueError("Duplicate Fusion entity named root")
