from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import KNestedHead
from convert.Formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord

# the nested form order must stay explicit so inconsistent revision links fail before history reconstruction
KNestedForm = ((7, "generic_tag_attrib_def"), *KNestedHead[:7])


# the nested tag decision must stay consistent so inconsistent revision links fail before history reconstruction
def IsNestedTag(Record: AsmRecord) -> bool:
    return (
        Record.Name == "ATTRIB_CUSTOM-attrib"
        and Record.Tokens[5 : 5 + len(KNestedForm)] == KNestedForm
    )


# invalid nest tags input must fail here so inconsistent revision links fail before history reconstruction
def CheckNestTags(
    Records: tuple[AsmRecord, ...], Versions: dict[int, int], Aliases: tuple[int, ...]
) -> None:
    for SlotId, Revision in Versions.items():
        Record = Records[Revision]
        if Record.Name != "ATTRIB_CUSTOM-attrib":
            continue
        ChildRef = ReadLiveRef(Record, 0, Aliases)
        if ChildRef != -1:
            Child = Records[Versions[ChildRef]]
            if not IsNestedTag(Child) or ReadLiveRef(Child, 4, Aliases) != SlotId:
                raise ValueError("Fusion nested tag attribute is not reciprocal")
        if IsNestedTag(Record):
            Parent = Records[Versions[ReadLiveRef(Record, 4, Aliases)]]
            if ReadLiveRef(Parent, 0, Aliases) != SlotId:
                raise ValueError("Fusion nested tag attribute is not reciprocal")
