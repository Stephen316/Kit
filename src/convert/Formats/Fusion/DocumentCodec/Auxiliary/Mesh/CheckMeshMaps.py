from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshLayout import (
    KGeometryGuid,
    KTextureGuid,
)
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap


# invalid mesh maps input must fail here so supporting records retain their owning document relationships
def CheckMeshMaps(Records: tuple[EntityRecord, ...]) -> None:
    KeyNames = {
        KGeometryGuid: ("textureIdToUuidMap",),
        KTextureGuid: ("uuidToTextureInfoMap", "uuidToTextureMap"),
    }
    for Record in Records:
        for Group in Record.Groups:
            Expected = KeyNames.get(Group.ClassGuid.upper(), ())
            Fields = {Field.FieldName: Field.Value for Field in Group.Fields}
            for KeyName in Expected:
                Value = Fields.get(KeyName)
                if not isinstance(Value, ValueMap) or Value.Entries:
                    raise ValueError(
                        "Document mesh textures require a qualified profile"
                    )
            if (
                Group.ClassGuid.upper() == KGeometryGuid
                and Fields.get("needsUpdate") is not False
            ):
                raise ValueError(
                    "Document mesh geometry requires an up-to-date component"
                )
