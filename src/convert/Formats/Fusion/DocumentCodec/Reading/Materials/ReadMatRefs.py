from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import (
    BindMaterials,
)
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import (
    ResolveMatAsset,
)
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the mat references operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
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


# resolve mat reference needs an explicit validity boundary so model state retains its native feature and ownership relationships
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
