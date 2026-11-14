from dataclasses import replace as ReplaceValue

from pytest import raises as ExpectError

from convert.formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.formats.Fusion.MaterialCodec.EncodeMaterials import EncodeMaterials
from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from tests.convert.formats.FusionCodec.Materials.ReadNative import ReadNative


def TestMissingLink() -> None:
    Native = ReadNative()
    Assets = DecodeMaterials(Native.Streams, Native.Schemas)
    Broken = tuple(
        ReplaceValue(
            Asset,
            Properties=tuple(
                (
                    ReplaceValue(
                        Entry, Connections=AssetLinks(True, ("missing-instance",))
                    )
                    if Entry.FieldName == "physmat_aspects"
                    else Entry
                )
                for Entry in Asset.Properties
            ),
        )
        for Asset in Assets
    )
    with ExpectError(ValueError, match="connection target is missing"):
        _ = EncodeMaterials(Broken, Native.Schemas)
