from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.Materials.BindMaterials import (
    BindMaterials,
)
from convert.formats.Fusion.DocumentCodec.Reading.Materials.CheckBodyMat import (
    CheckBodyMat,
)


def CheckDocMats(Value: DocumentModel) -> None:
    Managers = BindMaterials(Value)
    Roles = {
        "physicalMaterial": "physicalmaterial",
        "visualMaterial": "materialappearance",
    }
    for Segment in Value.Segments:
        if Segment.Metadata.Header.SegmentId != 0:
            continue
        for Record in Segment.Records:
            for Group in Record.Groups:
                for Field in Group.Fields:
                    if Field.FieldName in Roles and Field.Value is not None:
                        CheckBodyMat(Field.Value, Managers, Roles[Field.FieldName])
