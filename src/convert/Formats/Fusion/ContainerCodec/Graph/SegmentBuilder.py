from convert.Formats.Fusion.ContainerCodec.Graph.SegmentCatalog import SegmentCatalog
from convert.Formats.Fusion.ContainerCodec.Graph.EmitAuxiliary import EmitAuxiliary
from convert.Formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.MetaIndex import SegmentKind


# the segment builder contract needs a dedicated boundary so archive members retain their native ownership and reference relationships
class SegmentBuilder(SegmentCatalog):

    # segment builder needs explicit initial state so archive members retain their native ownership and reference relationships
    def __init__(
        self,
        Segment: SegmentKind,
        Schemas: tuple[NativeSchema, ...],
        External: EntityProfile,
    ) -> None:
        super().__init__(Segment, Schemas, External)
        self.Records: list[EntityRecord] = []

    # the value operation needs a consistent construction rule so archive members retain their native ownership and reference relationships
    def MakeValue(
        self, ClassName: str, Fields: dict[str, KEntityValue]
    ) -> ValueObject[KEntityValue]:
        return ValueObject(self.MakeGroups(ClassName, Fields))

    # the entity operation needs a consistent construction rule so archive members retain their native ownership and reference relationships
    def AddEntity(
        self,
        Identity: int,
        ClassName: str,
        Fields: dict[str, KEntityValue],
        RootName: str = "",
        Subjects: tuple[SubjectValue, ...] = (),
        SplitIndex: int | None = None,
    ) -> None:
        Groups = self.MakeGroups(ClassName, Fields)
        if SplitIndex is not None and not 0 < SplitIndex < len(Groups):
            raise ValueError("Invalid Fusion auxiliary continuation boundary")
        Primary = Groups[:SplitIndex]
        self.Records.append(
            EntityRecord(
                Identity,
                self.Codes[Primary[0].ClassGuid.upper()],
                True,
                EntityFrame(RootName, Subjects or None, None),
                Primary,
            )
        )
        if SplitIndex is not None:
            Following = Groups[SplitIndex:]
            self.Records.append(
                EntityRecord(
                    Identity,
                    self.Codes[Following[0].ClassGuid.upper()],
                    False,
                    EntityFrame(RootName, None, None),
                    Following,
                )
            )

    # finish needs one orchestration boundary so archive members retain their native ownership and reference relationships
    def Finish(self) -> AuxiliaryGraph:
        return EmitAuxiliary(
            self.Segment, self.Schemas, tuple(self.Records), self.Profile
        )
