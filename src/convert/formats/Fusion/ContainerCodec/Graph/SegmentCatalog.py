from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.ContainerCodec.Graph.MakeAuxGroups import MakeAuxGroups


class SegmentCatalog:
    def __init__(
        self,
        Segment: SegmentKind,
        Schemas: tuple[NativeSchema, ...],
        External: EntityProfile,
    ) -> None:
        super().__init__()
        self.Segment = Segment
        self.Schemas = tuple(
            sorted(Schemas, key=lambda Entry: Entry.Value.ClassGuid.upper())
        )
        self.ByName = {Entry.NameValue: Entry for Entry in self.Schemas}
        self.ByGuid = {Entry.Value.ClassGuid.upper(): Entry for Entry in self.Schemas}
        if len(self.ByName) != len(Schemas) or len(self.ByGuid) != len(Schemas):
            raise ValueError("Duplicate Fusion auxiliary schema")
        self.Codes = {
            Entry.Value.ClassGuid.upper(): Index
            for Index, Entry in enumerate(self.Schemas, 256)
        }
        Combined = {Entry.ClassGuid.upper(): Entry for Entry in External.Classes}
        for Entry in self.Schemas:
            Previous = Combined.get(Entry.Value.ClassGuid.upper())
            if Previous is not None and Previous != Entry.Value:
                raise ValueError("Fusion auxiliary and external schemas disagree")
            Combined[Entry.Value.ClassGuid.upper()] = Entry.Value
        self.Profile = EntityProfile(
            External.RootGuid, tuple(Combined.values()), External.ExternalTargets
        )

    def MakeGroups(
        self, ClassName: str, Fields: dict[str, KEntityValue]
    ) -> tuple[EntityGroup[KEntityValue], ...]:
        return MakeAuxGroups(
            self.ByName, self.ByGuid, self.Profile.RootGuid, ClassName, Fields
        )
