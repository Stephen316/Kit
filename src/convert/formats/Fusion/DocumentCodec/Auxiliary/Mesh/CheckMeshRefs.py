from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckMeshJoin import (
    CheckMeshJoin,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshLayout import (
    KBodyGuid,
    KGeometryGuid,
    KTriggerGuid,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshReference import (
    MeshReference,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def CheckMeshRefs(
    Records: tuple[EntityRecord, ...], Meshes: tuple[DocumentMesh, ...]
) -> None:
    Owners = {Record.ObjectId: Record for Record in Records if Record.IsPrimary}
    Parts = {PartValue.Name: PartValue for PartValue in Meshes}
    if len(Parts) != len(Meshes):
        raise ValueError("Document mesh component names are duplicated")
    Identities = {PartValue.Mesh.Registry.FusionId.lower() for PartValue in Meshes}
    if len(Identities) != len(Meshes):
        raise ValueError("Document mesh geometry UUIDs are duplicated")
    Joins: list[tuple[str, int]] = []
    Triggers: set[int] = set()
    for Record in Owners.values():
        ClassGuid = Record.Groups[0].ClassGuid.upper() if Record.Groups else ""
        if ClassGuid == KGeometryGuid:
            Joins.append(CheckMeshJoin(Record, Owners, Parts))
        elif ClassGuid == KTriggerGuid:
            Triggers.add(Record.ObjectId)
        elif ClassGuid == KBodyGuid:
            _ = MeshReference(
                GroupFields(Record.Groups).get("rMeshGeometry"), Owners, KGeometryGuid
            )
    Names = tuple(NameValue for NameValue, _ in Joins)
    TriggerIds = tuple(ObjectId for _, ObjectId in Joins)
    if len(set(Names)) != len(Names) or set(Names) != set(Parts):
        raise ValueError(
            "Document mesh parts disagree with all current and historical geometries"
        )
    if len(set(TriggerIds)) != len(TriggerIds) or set(TriggerIds) != Triggers:
        raise ValueError("Document mesh triggers are not uniquely owned by geometries")
