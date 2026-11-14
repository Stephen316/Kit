from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Records.DraftFrame import DraftFrame
from convert.formats.Fusion.DocumentCodec.Records.DraftGroups import DraftGroups
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord


def DraftRecords(
    Author: AuthorState, TypeCodes: dict[str, int]
) -> tuple[EntityRecord, ...]:
    Records: list[EntityRecord] = []
    for Entity in Author.Entities:
        Schema = Author.ByName[Entity.ClassName]
        Groups = DraftGroups(Author, Entity)
        SplitIndex = len(Groups)
        if Entity.ClassName == "MSketch":
            SplitIndex = 1
        elif Entity.ClassName == "FusionSketchLinearDim":
            SplitIndex = 2
        elif Schema.ClassSpace == "Fusion":
            SplitIndex = next(
                (
                    Index
                    for Index, Group in enumerate(Groups)
                    if Index
                    and Author.ByGuid[Group.ClassGuid.upper()].ClassSpace != "Fusion"
                ),
                len(Groups),
            )
        ObjectId = Author.Roles[Entity.RoleName]
        TypeCode = TypeCodes[Schema.Value.ClassGuid.upper()]
        Records.append(
            EntityRecord(
                ObjectId,
                TypeCode,
                True,
                DraftFrame(Author, Entity),
                Groups[:SplitIndex],
            )
        )
        if SplitIndex < len(Groups):
            Frame = EntityFrame(Entity.RootName, None, None)
            Records.append(
                EntityRecord(
                    ObjectId,
                    TypeCodes[Groups[SplitIndex].ClassGuid.upper()],
                    False,
                    Frame,
                    Groups[SplitIndex:],
                )
            )
    return tuple(Records)
