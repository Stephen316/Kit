from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue


def ChangeAssets(Assets: tuple[MaterialAsset, ...]) -> tuple[MaterialAsset, ...]:
    Result: list[MaterialAsset] = []
    for Asset in Assets:
        Properties: list[PropertyValue] = []
        for Entry in Asset.Properties:
            if Entry.FieldName in ("structural_Density", "thermal_Density"):
                assert isinstance(Entry.Value, UnitValue)
                Entry = ReplaceValue(
                    Entry, Value=ReplaceValue(Entry.Value, Magnitude=6300.0)
                )
            if Entry.FieldName == "metal_f0":
                Entry = ReplaceValue(Entry, Value=ColorValue(0.2, 0.4, 0.6, 1.0))
            Properties.append(Entry)
        Result.append(ReplaceValue(Asset, Properties=tuple(Properties)))
    return tuple(Result)
