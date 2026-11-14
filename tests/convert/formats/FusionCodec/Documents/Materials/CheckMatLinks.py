from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from tests.convert.formats.FusionCodec.Documents.Materials.MaterialFields import (
    MaterialFields,
)
from tests.convert.formats.FusionCodec.Documents.Rectangle.RectFields import RectFields


def CheckMatLinks(Model: DocumentModel) -> None:
    assert len(Model.Materials) == 1
    Assets = {Asset.InstanceId: Asset for Asset in Model.Materials[0].Package.Assets}
    Bodies = RectFields(Model, "Body")
    assert len(Bodies) == 1
    Physical = MaterialFields(Bodies[0]["physicalMaterial"])
    Visual = MaterialFields(Bodies[0]["visualMaterial"])
    for Fields, RoleName in (
        (Physical, "physicalmaterial"),
        (Visual, "materialappearance"),
    ):
        Identity = Fields["assetReference"]
        assert isinstance(Identity, str)
        Asset = Assets[Identity]
        assert Asset.AssetRole == RoleName
        assert Asset.DefinitionId == Fields["proteinMaterialID"]
        assert (
            dict((Field.FieldName, Field.Value) for Field in Asset.Properties)[
                "AssetLibID"
            ]
            == Fields["libraryID"]
        )
    Manager = RectFields(Model, "ProteinAssetManager")[0]
    assert Manager["PhysicalMaterialAssetReferences"] == ValueSeries(
        (Physical["assetReference"],)
    )
    assert Manager["VisualMaterialAssetReferences"] == ValueSeries(
        (Visual["assetReference"],)
    )
    assert Manager["PhysicalMaterialRefCountVector"] == ValueSeries((1,))
    assert Manager["VisualMaterialRefCountVector"] == ValueSeries((1,))
    Reference = Physical["ProteinAssetManager"]
    assert isinstance(Reference, LocalRef)
    assert Reference == Visual["ProteinAssetManager"]
    Record = next(
        Record
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if Record.IsPrimary and Record.ObjectId == Reference.ObjectId
    )
    Fields = {
        Field.FieldName: Field.Value
        for Group in Record.Groups
        for Field in Group.Fields
    }
    assert Model.Materials[0].Name == "ProteinAssets.BlobParts/" + str(
        Fields["partName"]
    )
