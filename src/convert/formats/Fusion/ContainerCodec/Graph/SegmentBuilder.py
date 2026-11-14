from convert.formats.Fusion.ContainerCodec.Graph.SegmentCatalog import SegmentCatalog
from convert.formats.Fusion.ContainerCodec.Graph.EmitAuxiliary import EmitAuxiliary
from convert.formats.Fusion.ContainerCodec.Model.AuxiliaryGraph import AuxiliaryGraph
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.MetaIndex import SegmentKind


class SegmentBuilder(SegmentCatalog):
    def __init__(
        self,
        Segment: SegmentKind,
        Schemas: tuple[NativeSchema, ...],
        External: EntityProfile,
    ) -> None:
        super().__init__(Segment, Schemas, External)
        self.Records: list[EntityRecord] = []

    def MakeValue(
        self, ClassName: str, Fields: dict[str, KEntityValue]
    ) -> ValueObject[KEntityValue]:
        return ValueObject(self.MakeGroups(ClassName, Fields))

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

    def Finish(self) -> AuxiliaryGraph:
        return EmitAuxiliary(
            self.Segment, self.Schemas, tuple(self.Records), self.Profile
        )
