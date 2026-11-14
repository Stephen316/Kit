from types import MappingProxyType as ReadOnlyMap

from convert.formats.Fusion.EntityCodec.Limits import KMaxCount, KMaxRecords
from convert.formats.Fusion.EntityCodec.Schema.CheckClass import CheckClass
from convert.formats.Fusion.EntityCodec.Schema.CheckWireType import CheckWireType
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.NamedTypes import NamedTypes
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def BindProfile(
    Profile: EntityProfile, Classes: tuple[MetaClass, ...]
) -> EntityCatalog:
    if not Profile.RootGuid or not 1 <= len(Profile.Classes) <= KMaxCount:
        raise ValueError("Invalid Fusion entity schema profile")
    Declared = {Schema.ClassGuid.upper(): Schema for Schema in Profile.Classes}
    if len(Declared) != len(Profile.Classes):
        raise ValueError("Duplicate Fusion entity schema identifier")
    LocalClasses: dict[int, str] = {}
    for Entry in Classes:
        Identity = Entry.ClassGuid.upper()
        Schema = Declared.get(Identity)
        if (
            Schema is None
            or Schema.SchemaVersion != Entry.SchemaVersion
            or Schema.BaseGuid.upper() != Entry.BaseGuid.upper()
        ):
            raise ValueError(
                "Fusion entity profile differs from archive class/version/base"
            )
        for ObjectId in Entry.OwnerIds:
            if (
                ObjectId in LocalClasses
                or type(ObjectId) is not int
                or not 0 <= ObjectId < 1 << 64
                or len(LocalClasses) >= KMaxRecords
            ):
                raise ValueError("Invalid or duplicate Fusion entity primary owner")
            LocalClasses[ObjectId] = Identity
    External = {
        (Target.SegmentId, Target.ObjectId): Target.ClassGuid.upper()
        for Target in Profile.ExternalTargets
    }
    if len(External) != len(Profile.ExternalTargets) or len(External) > KMaxRecords:
        raise ValueError("Invalid Fusion entity external target index")
    for SegmentId, ObjectId in External:
        if (
            type(SegmentId) is not int
            or not 0 <= SegmentId < 1 << 32
            or type(ObjectId) is not int
            or not 0 <= ObjectId < 1 << 64
        ):
            raise ValueError("Invalid Fusion entity external target identity")
    Catalog = EntityCatalog(
        Profile.RootGuid.upper(),
        ReadOnlyMap(Declared),
        ReadOnlyMap(LocalClasses),
        ReadOnlyMap(External),
        ReadOnlyMap(NamedTypes(Profile.NamedTypes)),
    )
    for Schema in Profile.Classes:
        CheckClass(Schema, Catalog)
    for Shape in Catalog.NamedTypes.values():
        CheckWireType(Shape, Catalog)
    return Catalog
