from dataclasses import replace as ReplaceValue
from io import BytesIO
from zipfile import ZipFile

from pytest import raises as ExpectError

from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from tests.convert.formats.FusionCodec.Bundles.BundleSource import BundleSource
from tests.convert.formats.FusionCodec.Bundles.ReadRelations import ReadRelations


def TestBundleGraph() -> None:
    Source = BundleSource().read_bytes()
    Bundle = ReadBundle(Source)
    Owners = {Entry.ObjectId: Entry for Entry in Bundle.Description.Graph.Objects}
    RootValue = Owners[Bundle.Description.Graph.RootIds[0]]
    Documents = {Entry.FileName: Entry.DataValue for Entry in Bundle.Documents}
    Expected = {
        (Owners[Relation.TargetId].MemberPath, Field.TextValue)
        for Group in RootValue.References
        for Relation in Group.Relations
        for Field in Relation.Metadata
        if Field.FieldName == "neutronRole"
    }
    assert len(Documents) == 9 and len(Expected) == 8
    assert ReadRelations(Documents[RootValue.MemberPath]) == Expected
    Output = EmitBundle(Bundle)
    with ZipFile(BytesIO(Output)) as Archive:
        assert Archive.testzip() is None
        assert all(
            Archive.read(NameValue) == DataValue
            for NameValue, DataValue in Documents.items()
        )
    assert ReadBundle(Output) == Bundle


def TestLostTarget() -> None:
    Bundle = ReadBundle(BundleSource().read_bytes())
    GraphValue = Bundle.Description.Graph
    ShortGraph = ReplaceValue(GraphValue, Objects=GraphValue.Objects[1:])
    Description = ReplaceValue(Bundle.Description, Graph=ShortGraph)
    with ExpectError(ValueError, match="reference targets"):
        _ = EmitBundle(ReplaceValue(Bundle, Description=Description))


def TestExtraMember() -> None:
    Stream = BytesIO(BundleSource().read_bytes())
    with ZipFile(Stream, "a") as Archive:
        Archive.writestr("extra.f3d", b"unindexed")
    with ExpectError(ValueError, match="members disagree"):
        _ = ReadBundle(Stream.getvalue())
