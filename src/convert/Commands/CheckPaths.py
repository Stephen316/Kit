from pathlib import Path as FilePath


def CheckPaths(Source: FilePath, Destination: FilePath | None) -> None:
    if not Source.is_file():
        raise ValueError("Source must be an existing regular file")
    if Source.stat().st_size > 256 * 1024 * 1024:
        raise ValueError(
            "CLI source size exceeds the 256 MiB limit; use the SDK for larger inputs"
        )
    if Destination is None:
        return
    if Source.resolve() == Destination.resolve() or (
        Destination.exists() and Source.samefile(Destination)
    ):
        raise ValueError("Source and destination must be different files")
