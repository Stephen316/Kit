from pathlib import Path as FilePath
from struct import pack as PackValue
from zipfile import ZipFile


def CorruptScene(Source: FilePath, Target: FilePath, Variant: str) -> None:
    Prefix = "FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/"
    Changed = False
    with ZipFile(Source) as Original, ZipFile(Target, "w") as Result:
        for Entry in Original.infolist():
            Payload = Original.read(Entry)
            if Entry.filename == Prefix + "world":
                if Variant == "world-tail":
                    Payload += b"\x00"
                    Changed = True
                elif Variant == "version":
                    Token = "GraphicsGlobalVersion".encode("utf-16le")
                    Marker = PackValue("<I", len(Token) // 2) + Token
                    Offset = Payload.index(Marker) + len(Marker)
                    assert Payload[Offset : Offset + 4] == PackValue("<I", 1)
                    Payload = (
                        Payload[:Offset] + PackValue("<I", 2) + Payload[Offset + 4 :]
                    )
                    Changed = True
            elif (
                Entry.filename == Prefix + "stream_mesh_000" and Variant == "mesh-tail"
            ):
                Payload += b"\x00"
                Changed = True
            Result.writestr(Entry.filename, Payload)
    assert Changed
