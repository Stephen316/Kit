from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.Materials.BindManager import (
    BindManager,
)
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


def BindMaterials(Value: DocumentModel) -> dict[int, MaterialPackage]:
    Parts = {PartValue.Name: PartValue for PartValue in Value.Materials}
    if len(Parts) != len(Value.Materials):
        raise ValueError("Duplicate document material part")
    Records = tuple(
        Record
        for Segment in Value.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
    )
    Managers = [
        Record.ObjectId
        for Record in Records
        if Record.Frame.RootId == "ProteinAssetManager"
    ]
    Result: dict[int, MaterialPackage] = {}
    Bound: set[str] = set()
    for Identity in Managers:
        Groups = tuple(
            Group
            for Record in Records
            if Record.ObjectId == Identity
            for Group in Record.Groups
        )
        PartName, Package = BindManager(GroupFields(Groups), Parts)
        if Package is not None:
            Result[Identity] = Package
            Bound.add(PartName)
    if Bound != set(Parts):
        raise ValueError("Document material package lacks a manager reference")
    return Result
