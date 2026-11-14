from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import (
    ResolveMatAsset,
)
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def CheckBodyMat(
    Value: KEntityValue, Managers: dict[int, MaterialPackage], RoleName: str
) -> None:
    if isinstance(Value, OptionalValue):
        Value = Value.Value
    if Value is None:
        return
    if not isinstance(Value, ValueObject):
        raise ValueError("Invalid document body material value")
    Fields = GroupFields(Value.Groups)
    Identity, Reference = Fields.get("assetReference"), Fields.get(
        "ProteinAssetManager"
    )
    if Identity == "" and Reference is None:
        return
    if (
        not isinstance(Identity, str)
        or not isinstance(Reference, (LocalRef, SegmentRef))
        or isinstance(Reference, SegmentRef)
        and Reference.SegmentId != 0
    ):
        raise ValueError("Invalid document body material reference")
    Package = Managers.get(Reference.ObjectId)
    if Package is None:
        raise ValueError("Body material manager has no package")
    Asset = ResolveMatAsset(Package, Identity)
    if (
        Asset is None
        or Asset.AssetRole != RoleName
        or Fields.get("proteinMaterialID") != Asset.DefinitionId
    ):
        raise ValueError("Body material references a missing or incompatible asset")
    Libraries = [
        Property.Value
        for Property in Asset.Properties
        if Property.FieldName == "AssetLibID"
    ]
    if len(Libraries) != 1 or Fields.get("libraryID") != Libraries[0]:
        raise ValueError("Body material library identity disagrees with its asset")
