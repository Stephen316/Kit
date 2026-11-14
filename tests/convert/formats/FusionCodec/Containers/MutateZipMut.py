from dataclasses import replace as Replace

from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SegmentCodec.Metadata.WriteMetaWire import WriteMetaWire


def MutateZipMut(Members: dict[str, bytes], Mutation: str) -> None:
    if Mutation == "directory":
        del Members["FusionAssetName[Active]/Breps.BlobParts/"]
    elif Mutation == "unknown":
        Members["Unknown.dat"] = b"uninterpreted"
    elif Mutation == "case_alias":
        Members["manifest.dat"] = Members["Manifest.dat"]
    elif Mutation == "identity":
        RootValue = ReadRootWire(Members["Manifest.dat"])
        Members["Manifest.dat"] = EmitRootWire(
            Replace(RootValue, AssetId="31415926-1111-4222-8333-0123456789ab")
        )
    elif Mutation == "watermark":
        NameValue = "FusionAssetName[Active]/Manifest.dat"
        Payload = Members[NameValue]
        Marker = b"\0\0\0\0\3\0\0\0\3\0\0\0"
        assert Payload.count(Marker) == 1
        Members[NameValue] = Payload.replace(Marker, b"\0" * 8 + b"\3\0\0\0")
    elif Mutation == "offsets":
        NameValue = "FusionAssetName[Active]/FusionDesignSegmentType1/MetaStream.dat"
        Metadata = ReadMetaWire(Members[NameValue])
        First, Second, *Following = Metadata.Primary
        Primary = (
            Replace(First, Offset=Second.Offset),
            Replace(Second, Offset=First.Offset),
            *Following,
        )
        Members[NameValue] = WriteMetaWire(Replace(Metadata, Primary=Primary))
    elif Mutation == "preview":
        NameValue = "FusionAssetName[Active]/Previews/small.png"
        Members[NameValue] = Members[NameValue][:-1]
