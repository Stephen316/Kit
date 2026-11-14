from dataclasses import replace as ReplaceValue

from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Manifest.AssetLink import AssetLink
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingSlot import DrawingSlot
from convert.formats.Fusion.DrawingCodec.Manifest.EmitAsset import EmitAsset
from convert.formats.Fusion.DrawingCodec.Manifest.EmitRoot import EmitRoot
from convert.formats.Fusion.DrawingCodec.Manifest.ReadAsset import ReadAsset
from convert.formats.Fusion.DrawingCodec.Manifest.ReadRoot import ReadRoot
from convert.formats.Fusion.DrawingCodec.Manifest.RootAsset import RootAsset
from convert.formats.Fusion.DrawingCodec.Manifest.RootLink import RootLink

KAssetId = "5c99c6f1-54e3-4150-9edd-ca384be2cba6"

KRoleId = "6a5f6318-0a66-4894-917d-ee31c5e9b85c"


def ModernRoot() -> DrawingRoot:
    LinkValue = RootLink(
        KRoleId,
        None,
        "C:/KitFixture/W.login/F/Drawing.f2d",
        "C:/KitFixture/W.login/F/Source.f3d",
        "C:/KitFixture/W.login/F/_XRef_/Source_LV1.f3d",
        (3, 4, 1, 0),
        (("toDocDisplayName", "Source"), ("linkClassification", "OriginalDesign")),
    )
    return DrawingRoot(
        "FusionDrawingDocType",
        ".f2d",
        "Fusion Drawing Document",
        "Drawing Document",
        "52f5de6e-e139-4c24-a301-589ae75faf34",
        "85b6a6ff-2bf1-4323-977d-feccc4bb7d1b",
        1234,
        20,
        3046685422794047505,
        (("Application", 2),),
        ("85b6a6ff-2bf1-4323-977d-feccc4bb7d1b",),
        True,
        (LinkValue,),
        KAssetId,
        (RootAsset("Documentation", 0, 0),),
        "Source Drawing",
        "NA_OFFLINESAVE",
    )


def ModernAsset() -> DrawingAsset:
    return DrawingAsset(
        "Documentation",
        KAssetId,
        "e02d738e-929d-4927-86f6-bd96ded53876",
        "FusionDrawingAssetType",
        20,
        (("Application", 4), ("Server", 36)),
        "Neutron3DAssetType",
        (
            AssetLink(
                KRoleId,
                "1a3a8859-af3b-4c73-940f-0b4121727ae8",
                "36653466-f312-447e-b620-40b11fb1d5a9",
            ),
        ),
        1,
        3,
        "380c54b1-d30f-4ca4-a58e-fc09c5e19bf5",
        5,
        (
            DrawingSlot(
                0, "FusionDrawingDesignSegmentType", "FusionDrawingDesignSegmentType"
            ),
            DrawingSlot(
                1, "FusionDrawingACTSegmentType", "FusionDrawingACTSegmentType"
            ),
        ),
    )


def TestModernRoot() -> None:
    Value = ModernRoot()
    Payload = EmitRoot(Value)
    assert ReadRoot(Payload) == Value
    with ExpectError(ValueError):
        _ = ReadRoot(Payload + b"\x00")
    with ExpectError(ValueError, match="disagree with its version"):
        _ = EmitRoot(ReplaceValue(Value, SaveLabel=None))
    with ExpectError(ValueError, match="reference marker"):
        _ = EmitRoot(ReplaceValue(Value, HasReferences=False))
    with ExpectError(ValueError, match="Unsupported Fusion drawing manifest version"):
        _ = EmitRoot(ReplaceValue(Value, Version=15))


def TestLegacyRoot() -> None:
    Modern = ModernRoot()
    LinkValue = ReplaceValue(
        Modern.References[0], Role=KRoleId + "_urn:adsk.wipdata:x", Unresolved=""
    )
    Value = ReplaceValue(
        Modern,
        Magic=0x080006A7,
        Version=10,
        Software=None,
        SaveLabel=None,
        References=(LinkValue,),
    )
    assert ReadRoot(EmitRoot(Value)) == Value
    with ExpectError(ValueError, match="reference fields"):
        _ = EmitRoot(ReplaceValue(Value, References=(Modern.References[0],)))


def TestModernAsset() -> None:
    Value = ModernAsset()
    Payload = EmitAsset(Value)
    assert ReadAsset(Payload) == Value
    Legacy = ReplaceValue(
        Value, Version=10, Allocation=2, ChangeGuid=None, ChangeWord=None
    )
    assert ReadAsset(EmitAsset(Legacy)) == Legacy
    with ExpectError(ValueError, match="disagree with its version"):
        _ = EmitAsset(ReplaceValue(Value, ChangeGuid=None))
    Twice = Value.Segments[:1] * 2
    with ExpectError(ValueError, match="Duplicate"):
        _ = EmitAsset(ReplaceValue(Value, Segments=Twice))
    with ExpectError(ValueError, match="Expected a typed"):
        _ = EmitAsset(ReplaceValue(Value, Version=21))
