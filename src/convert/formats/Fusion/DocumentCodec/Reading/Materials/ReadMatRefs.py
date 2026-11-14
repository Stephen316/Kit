from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import (
    BindMaterials,
)
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import (
    ResolveMatAsset,
)
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def ReadMatRefs(
    Value: DocumentModel, FieldName: str
) -> tuple[tuple[MaterialPackage | None, str], ...]:
    Managers = BindMaterials(Value)
    Result: list[tuple[MaterialPackage | None, str]] = []
    for Segment in Value.Segments:
        if Segment.Metadata.Header.SegmentId != 0:
            continue
        for Record in Segment.Records:
            for Group in Record.Groups:
                for Field in Group.Fields:
                    if Field.FieldName != FieldName:
                        continue
                    Found = ResolveMatRef(Field.Value, Managers)
                    if Found is not None and not any(
                        Found[0] is Known[0] and Found[1] == Known[1]
                        for Known in Result
                    ):
                        Result.append(Found)
    return tuple(Result)


def ResolveMatRef(
    Value: KEntityValue, Managers: dict[int, MaterialPackage]
) -> tuple[MaterialPackage | None, str] | None:
    if isinstance(Value, OptionalValue):
        Value = Value.Value
    if not isinstance(Value, ValueObject):
        return None
    Fields = GroupFields(Value.Groups)
    Identity = Fields.get("assetReference")
    Reference = Fields.get("ProteinAssetManager")
    if Identity == "" and Reference is None:
        return None, ""
    if not isinstance(Identity, str) or not isinstance(
        Reference, (LocalRef, SegmentRef)
    ):
        raise ValueError("Invalid Fusion material reference")
    Package = Managers.get(Reference.ObjectId)
    Asset = None if Package is None else ResolveMatAsset(Package, Identity)
    if Package is None or Asset is None:
        raise ValueError("Fusion material reference has no asset")
    return Package, Asset.InstanceId
