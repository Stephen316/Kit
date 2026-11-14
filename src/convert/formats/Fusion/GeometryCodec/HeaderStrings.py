from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def HeaderStrings(Stamp: GeometryStamp) -> str:
    return " ".join(
        f"{len(Value.encode('utf-8'))} {Value}"
        for Value in (Stamp.Product, Stamp.Version, Stamp.SavedAt)
    )
