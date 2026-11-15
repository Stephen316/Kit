from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


# invalid roots input must fail here so entity identifiers retain their schema and reference meaning
def CheckRoots(Records: tuple[EntityRecord, ...]) -> None:
    Names = tuple(
        Record.Frame.RootId
        for Record in Records
        if Record.IsPrimary and Record.Frame.RootId
    )
    if len(set(Names)) != len(Names):
        raise ValueError("Duplicate Fusion entity named root")
