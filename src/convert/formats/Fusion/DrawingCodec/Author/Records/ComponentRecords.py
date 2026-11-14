from convert.formats.Fusion.DrawingCodec.Author.Defaults.ComponentGroup import (
    KComponentGroup,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingIdentity import (
    DrawingIdentity,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.RecordTools import (
    MakeRecord,
    ObjectTail,
)
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KInstanceGates = (
    NamedMetadata("GatedByParent", "IntrinsicMetaTypebool", False),
    NamedMetadata("ResolutionTime", "IntrinsicMetaTypeHString", ""),
    NamedMetadata("SelfGated", "IntrinsicMetaTypebool", False),
)

KMaterialValue = ValueObject(
    (
        EntityGroup(
            "A62C82F6-7CF7-4FF3-9C12-D87FF3965C9C",
            (
                NamedValue("ProteinAssetManager", None),
                NamedValue("assetReference", ""),
                NamedValue("libraryID", ""),
                NamedValue("name", ""),
                NamedValue("proteinMaterialID", ""),
            ),
        ),
    )
)


def ComponentRecord(
    Identity: DrawingIdentity, CycleColor: tuple[float, float, float]
) -> EntityRecord:
    RedValue, GreenValue, BlueValue = CycleColor
    ColorValue = ValueStruct(
        (
            NamedValue("red", RedValue),
            NamedValue("green", GreenValue),
            NamedValue("blue", BlueValue),
            NamedValue("alpha", 1.0),
        )
    )
    Fields = (
        NamedValue("createdPreACT", False),
        NamedValue("creationIndex", 0),
        NamedValue("cyclingColor", ColorValue),
        NamedValue("defaultPhysicalMaterial", KMaterialValue),
        NamedValue("isVisible", True),
        NamedValue("overrides", LocalRef(2)),
        NamedValue("persistentId", Identity.ComponentGuid),
        NamedValue("rACTComponent", SegmentRef(1, 1)),
        NamedValue("rComponentBaseInstances", LocalRef(3)),
        NamedValue("rOwningDeriveFeature", None),
        NamedValue("revisionGuid", Identity.ComponentRevision),
        NamedValue("userName", ""),
    )
    return MakeRecord(
        0,
        (
            KComponentGroup,
            EntityGroup("EAF14CD0-75FD-4770-9C01-ABF1A66C2BCA", Fields),
            *ObjectTail(LocalRef(20)),
        ),
        Metadata=(),
    )


def InstanceRecord(Identity: DrawingIdentity, InstanceGates: bool) -> EntityRecord:
    Fields = (
        NamedValue("bGroundToParent", False),
        NamedValue("bRigidSubAssembly", False),
        NamedValue("creationIndex", 0),
        NamedValue("initialTransform", MatrixValue(None)),
        NamedValue("lastSavedTargetRevisionGuid", Identity.ComponentRevision),
        NamedValue("persistentId", Identity.InstanceGuid),
        NamedValue("rACTInstance", SegmentRef(4, 1)),
        NamedValue("rOwningDeriveFeature", None),
        NamedValue("rTargetComponent", LocalRef(0)),
        NamedValue("transform", MatrixValue(None)),
        NamedValue("userName", ""),
        NamedValue("xAssetLinkName", ""),
    )
    return MakeRecord(
        20,
        (
            EntityGroup("CE2913AA-CFE0-4F04-9102-24424ED3BCFA", ()),
            EntityGroup("D4CBC599-0FFB-4d32-BF14-A7F0AFA25013", Fields),
            *ObjectTail(None),
        ),
        RootId="rootInstance",
        Subjects=(SubjectValue(LocalRef(0), 0),),
        Metadata=KInstanceGates if InstanceGates else None,
    )
