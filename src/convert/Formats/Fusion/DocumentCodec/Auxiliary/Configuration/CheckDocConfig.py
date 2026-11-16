from convert.Formats.Fusion.AssetCodec.ConfigLayout import KConfigClasses
from convert.Formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)


# invalid doc config input must fail here so supporting records retain their owning document relationships
def CheckDocConfig(Value: DocumentModel) -> None:
    CheckConfigRefs(Value.Segments, Value.Configurations)


# invalid config references input must fail here so supporting records retain their owning document relationships
def CheckConfigRefs(
    Segments: tuple[ParsedSegment, ...], Configurations: tuple[ConfigPart, ...]
) -> None:
    Expected: list[str] = []
    for Segment in Segments:
        if Segment.Metadata.Header.SegmentId != 0:
            continue
        for Record in Segment.Records:
            Matches = [
                KConfigClasses[Group.ClassGuid.upper()]
                for Group in Record.Groups
                if Group.ClassGuid.upper() in KConfigClasses
            ]
            if not Matches:
                continue
            if (
                len(Matches) != 1
                or not Record.IsPrimary
                or Record.Frame.RootId != Matches[0][0] + "SerializerTrigger"
            ):
                raise ValueError("Invalid configuration serializer trigger")
            PartName = GroupFields(Record.Groups).get("partName")
            if (
                not isinstance(PartName, str)
                or not PartName.startswith(Matches[0][0] + ".")
                or not PartName.endswith(Matches[0][1])
            ):
                raise ValueError("Configuration trigger has an invalid part name")
            Expected.append("DesignConfigurationTable.BlobParts/" + PartName)
    Names = tuple(PartValue.Name for PartValue in Configurations)
    if (
        len(Expected) != len(Names)
        or set(Expected) != set(Names)
        or len(set(Names)) != len(Names)
    ):
        raise ValueError("Configuration parts disagree with Design triggers")
    if Names and (
        len(Names) != 2
        or {PartValue.KindValue for PartValue in Configurations} != {"table", "rule"}
    ):
        raise ValueError("Configurations require one table and one rule")
