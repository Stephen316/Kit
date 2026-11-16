from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


# the header strings contract needs a shared interpretation so geometric values retain their native record boundaries
def HeaderStrings(Stamp: GeometryStamp) -> str:
    return " ".join(
        f"{len(Value.encode('utf-8'))} {Value}"
        for Value in (Stamp.Product, Stamp.Version, Stamp.SavedAt)
    )
