from pathlib import Path as FilePath


# path and memory inputs share the same bounded native archive contract
def LoadFusionBytes(SourceData: str | FilePath | bytes) -> tuple[bytes, str]:
    if isinstance(SourceData, bytes):
        return SourceData, ""
    SourcePath = FilePath(SourceData).expanduser().resolve()
    with SourcePath.open("rb") as SourceFile:
        DataValue = SourceFile.read(128 * 1024 * 1024 + 1)
    if len(DataValue) > 128 * 1024 * 1024:
        raise ValueError("Fusion ZIP exceeds input size limit")
    return DataValue, str(SourcePath)
