from base64 import b64encode as EncodeBase

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip


def FusionView(Payload: bytes, StreamName: str | None) -> dict[str, object]:
    with OpenFusionZip(Payload) as Archive:
        Result: dict[str, object] = {
            "format": "fusion.f3d",
            "layer": "container",
            "members": [
                {
                    "name": Value.Name,
                    "offset": Value.HeaderOffset,
                    "size": Value.Size,
                    "compressed_size": Value.CompressedSize,
                    "compression_method": Value.Method,
                    "crc32": Value.Crc,
                    "directory": Value.IsDirectory,
                }
                for Value in Archive.Members
            ],
        }
        if StreamName is not None:
            Result["stream"] = {
                "name": StreamName,
                "encoding": "base64",
                "data": EncodeBase(
                    Archive.ReadMember(StreamName, 16 * 1024 * 1024)
                ).decode("ascii"),
            }
        return Result
