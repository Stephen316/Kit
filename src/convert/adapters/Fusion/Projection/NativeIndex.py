from dataclasses import dataclass as MakeDataClass
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import AuthorSchemas
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MetaIndex import SegmentKind


# native index needs an explicit state contract so public document claims remain grounded in native records
@MakeDataClass(frozen=True, slots=True)
class NativeIndex:
    Segment: ParsedSegment
    Names: dict[str, tuple[int, ...]]
    Fields: dict[int, dict[str, KEntityValue]]

    # find one must resolve unambiguously so public document claims remain grounded in native records
    def FindOne(self, NameValue: str) -> dict[str, KEntityValue]:
        Identities = self.Names.get(NameValue, ())
        if len(Identities) != 1:
            raise ValueError(f"Qualified Fusion projection requires one {NameValue}")
        return self.Fields[Identities[0]]


# the index operation needs a consistent construction rule so public document claims remain grounded in native records
def MakeIndex(ModelValue: DocumentModel) -> NativeIndex:
    Segments = tuple(
        ItemValue
        for ItemValue in ModelValue.Segments
        if ItemValue.Metadata.Header.Segment == SegmentKind.KDesign
    )
    if (
        len(Segments) != 1
        or ModelValue.Configurations
        or ModelValue.Snapshots
        or ModelValue.Graphics is not None
    ):
        raise ValueError(
            "Fusion adapter requires one design without auxiliary configurations, snapshots or graphics"
        )
    Names = {
        Schema.Value.ClassGuid.upper(): Schema.NameValue
        for Schema in AuthorSchemas("cuboid", True)
    }
    Records = Segments[0].Records
    Identities: dict[str, tuple[int, ...]] = {}
    for Record in Records:
        if Record.IsPrimary:
            NameValue = Names.get(Record.Groups[0].ClassGuid.upper())
            if NameValue is None:
                raise ValueError("Unsupported native Fusion feature class")
            Identities[NameValue] = Identities.get(NameValue, ()) + (Record.ObjectId,)
    Fields = {
        Record.ObjectId: RecordFields(Records, Record.ObjectId)
        for Record in Records
        if Record.IsPrimary
    }
    return NativeIndex(Segments[0], Identities, Fields)


# the record fields contract needs a shared interpretation so public document claims remain grounded in native records
def RecordFields(
    Records: tuple[EntityRecord, ...], Identity: int
) -> dict[str, KEntityValue]:
    return {
        Field.FieldName: Field.Value
        for Record in Records
        if Record.ObjectId == Identity
        for Group in Record.Groups
        for Field in Group.Fields
    }


# struct fields needs an explicit validity boundary so public document claims remain grounded in native records
def StructFields(Value: KEntityValue) -> dict[str, KEntityValue]:
    if not isinstance(Value, ValueStruct):
        raise ValueError("Qualified Fusion projection requires a typed structure")
    return {Field.FieldName: Field.Value for Field in Value.Fields}


# native text needs an explicit validity boundary so public document claims remain grounded in native records
def NativeText(Value: KEntityValue) -> str:
    if not isinstance(Value, str):
        raise ValueError("Qualified Fusion projection requires text")
    return Value


# native number needs an explicit validity boundary so public document claims remain grounded in native records
def NativeNumber(Value: KEntityValue) -> float:
    if type(Value) not in (float, int):
        raise ValueError("Qualified Fusion projection requires a numeric value")
    return float(CastValue(float | int, Value))
