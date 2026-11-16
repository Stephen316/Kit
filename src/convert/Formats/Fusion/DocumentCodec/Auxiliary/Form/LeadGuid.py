from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


# the lead guid contract needs a shared interpretation so supporting records retain their owning document relationships
def LeadGuid(Record: EntityRecord) -> str:
    return Record.Groups[0].ClassGuid.upper() if Record.Groups else ""
