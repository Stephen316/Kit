from convert.formats.Fusion.MaterialCodec.DecodeMaterials import DecodeMaterials
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from tests.convert.formats.FusionCodec.Materials.ReadNative import ReadNative


def TestNativeProps() -> None:
    Native = ReadNative()
    Assets = DecodeMaterials(Native.Streams, Native.Schemas)
    assert len(Assets) == 6
    assert sum(len(Asset.Properties) for Asset in Assets) == 168
    assert sum(len(Asset.Definitions) for Asset in Assets) == 48
    Properties = {
        Entry.FieldName: Entry for Asset in Assets for Entry in Asset.Properties
    }
    assert Properties["structural_Density"].Value == UnitValue(69633, 7850.0)
    assert Properties["thermal_Density"].Value == UnitValue(69633, 7850.0)
    assert Properties["structural_Poisson_ratio"].Value == UnitValue(4097, 0.3)
    Links = Properties["physmat_aspects"].Connections
    assert Links is not None and Links.Enabled and len(Links.Targets) == 3
    assert set(Links.Targets) <= {Asset.InstanceId for Asset in Assets}
    assert any(Asset.InstanceId.endswith("_Post2015") for Asset in Assets)
    Appearance = next(
        Asset for Asset in Assets if Asset.SchemaName == "PrismMetalSchema"
    )
    Version = next(
        Entry.Value
        for Entry in Appearance.Definitions
        if Entry.FieldName == "VersionGUID"
    )
    assert Appearance.DefinitionId == "PrismMaterial-018_physmat_aspects:Prism-256"
    assert Version == "Prism-256"
