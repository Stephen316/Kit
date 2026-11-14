from dataclasses import replace as ReplaceValue

from pytest import mark as MarkTests, raises as RaisesError
from sys import version_info as PythonVersion

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Documents.Graphics.GraphicsSources import (
    KGraphicSources,
)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestAliasReject() -> None:
    Model = ReadDocument(KGraphicSources[0].read_bytes())
    assert len(Model.Materials) == 1
    Material = Model.Materials[0]
    Selected = next(
        Asset
        for Asset in Material.Package.Assets
        if Asset.InstanceId.endswith("_Post2015")
    )
    Changed = ReplaceValue(Selected, AssetRole="physicalmaterial")
    Assets = tuple(
        Changed if Asset.InstanceId == Selected.InstanceId else Asset
        for Asset in Material.Package.Assets
    )
    Package = ReplaceValue(Material.Package, Assets=Assets)
    Modified = ReplaceValue(Model, Materials=(ReplaceValue(Material, Package=Package),))
    with RaisesError(ValueError, match="missing or incompatible asset"):
        _ = EmitParsed(Modified)
