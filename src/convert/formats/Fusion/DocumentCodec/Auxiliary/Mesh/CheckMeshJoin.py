from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshLayout import (
    KBlobGuid,
    KGeometryGuid,
    KMeshFolder,
    KTriggerGuid,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshName import MeshName
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshReference import (
    MeshReference,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def CheckMeshJoin(
    Geometry: EntityRecord,
    Owners: dict[int, EntityRecord],
    Parts: dict[str, DocumentMesh],
) -> tuple[str, int]:
    Fields = GroupFields(Geometry.Groups)
    Trigger = MeshReference(Fields.get("rSerializerTrigger"), Owners, KTriggerGuid)
    if KBlobGuid not in {Group.ClassGuid.upper() for Group in Trigger.Groups}:
        raise ValueError("Mesh serializer trigger lacks its blob declaration")
    Links = GroupFields(Trigger.Groups)
    Target = MeshReference(Links.get("rMeshGeometry"), Owners, KGeometryGuid)
    if Target.ObjectId != Geometry.ObjectId:
        raise ValueError("Mesh geometry and serializer trigger are not reciprocal")
    PartName, Identity = Links.get("partName"), Fields.get("pMeshUuid")
    if not isinstance(PartName, str) or not isinstance(Identity, str):
        raise ValueError("Mesh geometry requires a part name and UUID")
    NameValue = KMeshFolder + PartName
    _ = MeshName(NameValue)
    PartValue = Parts.get(NameValue)
    if PartValue is None:
        raise ValueError("Mesh geometry references a missing component")
    if PartValue.Mesh.Registry.FusionId.lower() != Identity.lower():
        raise ValueError("Mesh geometry UUID disagrees with its component")
    return NameValue, Trigger.ObjectId
