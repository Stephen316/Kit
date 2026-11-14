from re import fullmatch as FullMatch

KGraphicPath = (
    r"OGS\.BlobFolder/OGS/DefaultScene/"
    + r"(world|stream_mesh_[0-9]{3}|Fusion_mesh_[0-9]{3})"
)


def IsGraphicPath(NameValue: str) -> bool:
    return FullMatch(KGraphicPath, NameValue) is not None
