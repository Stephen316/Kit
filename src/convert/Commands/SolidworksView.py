from base64 import b64encode as EncodeBase

from convert.adapters.solidworks.container.Container import SldprtArchive


# compressed container inspection needs bounded decoded evidence before exposing archive members
def SolidworksView(
    Payload: bytes, StreamName: str | None, FormatId: str
) -> dict[str, object]:
    Archive = SldprtArchive.FromBytes(Payload, SizeLimit=128 * 1024 * 1024)
    Result: dict[str, object] = {
        "format": FormatId,
        "layer": "container",
        "file_id": Archive.file_id,
        "container_version": Archive.format_version,
        "members": [
            {
                "name": Value.name,
                "offset": Value.offset,
                "payload_offset": Value.payload_offset,
                "size": Value.uncompressed_size,
                "compressed_size": Value.compressed_size,
                "crc32": Value.crc32,
            }
            for Value in Archive.records
        ],
    }
    if StreamName is not None:
        Payload = Archive.Require(StreamName)
        if len(Payload) > 16 * 1024 * 1024:
            raise ValueError("Container stream exceeds the 16 MiB limit")
        Result["stream"] = {
            "name": StreamName,
            "encoding": "base64",
            "data": EncodeBase(Payload).decode("ascii"),
        }
    return Result
