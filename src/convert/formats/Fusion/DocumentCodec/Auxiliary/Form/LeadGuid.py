from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def LeadGuid(Record: EntityRecord) -> str:
    return Record.Groups[0].ClassGuid.upper() if Record.Groups else ""
