from re import fullmatch as FullMatch

# graphic path needs a stable location so container reconstruction resolves inputs independently of the caller working directory
KGraphicPath = (
    r"OGS\.BlobFolder/OGS/DefaultScene/"
    + r"(world|stream_mesh_[0-9]{3}|Fusion_mesh_[0-9]{3})"
)


# the graphic path decision must stay consistent so archive members retain their native ownership and reference relationships
def IsGraphicPath(NameValue: str) -> bool:
    return FullMatch(KGraphicPath, NameValue) is not None
