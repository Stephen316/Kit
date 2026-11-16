from convert.Formats.Fusion.DocumentCodec.Auxiliary.Images.CheckImagePart import (
    CheckImagePart,
    KImageFolder,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)

# image class must remain consistent across callers so supporting records retain their owning document relationships
KImageClass = "830A2A2B-0AA9-4D6A-ACA1-F7A2B2A06573"


# invalid doc images input must fail here so supporting records retain their owning document relationships
def CheckDocImages(Value: DocumentModel) -> None:
    Expected: list[str] = []
    for Segment in Value.Segments:
        if Segment.Metadata.Header.SegmentId != 0:
            continue
        for Record in Segment.Records:
            if all(Group.ClassGuid.upper() != KImageClass for Group in Record.Groups):
                continue
            PartName = GroupFields(Record.Groups).get("partName")
            if not isinstance(PartName, str):
                raise ValueError("Fusion image serializer has an invalid part name")
            if PartName:
                Expected.append(KImageFolder + PartName)
    Names = tuple(CheckImagePart(Image).Name for Image in Value.Images)
    if sorted(Expected) != sorted(Names) or len(set(Names)) != len(Names):
        raise ValueError("Fusion image parts disagree with Design serializers")
