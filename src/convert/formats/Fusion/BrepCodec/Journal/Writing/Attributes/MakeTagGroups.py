from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakeTagGroups(Groups: tuple[FeatureTag, ...]) -> tuple[KAsmToken, ...]:
    Fields: list[KAsmToken] = [
        (4, 3),
        (4, 3),
        (4, -1),
        (7, "generic_tag_attrib_def "),
        (4, len(Groups)),
    ]
    for Group in Groups:
        Fields.extend(
            (
                (4, len(Group.PrimaryId.encode("ascii"))),
                (7, Group.PrimaryId),
                (4, Group.SecondaryId),
                (4, len(Group.OperationIds)),
            )
        )
        Fields.extend((4, Value) for Value in Group.OperationIds)
        Fields.append((4, Group.ApproachId))
    return tuple(Fields)
