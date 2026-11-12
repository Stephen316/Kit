from dataclasses import replace as Replace
from io import BytesIO
from math import pi as CirclePi
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from pytest import raises as Raises

from convert.adapters.base import ParseUntrusted
from convert.adapters.freecad.Adapter import DocToManifest
from convert.adapters.freecad.Archive import MakePlacement
from convert.adapters.freecad.ArchiveOutput.ArchiveWrite import BuildFcstdMut
from convert.adapters.freecad.EditDatum.DatumBinding import KDatumBinding
from convert.adapters.freecad.EditDatum.ReconcileDatum import ReconcileDatum
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.BoundPlaneValues import GetDatumFrame
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter, ParameterValue
from interchange.records.RecordSource import CadSource
from interchange.serialization.EncodeData import ToData


# a typed independent datum gives the writer a finite owned scalar and reference pose
def MakeDatumDoc(Method: str) -> CadDocument:
    Reference = Transform(origin=SpaceVector(2.0, 3.0, -5.0))
    Definition = BoundDatum("support", "scalar", "extra", Method, Reference)
    Feature = FeatureStep(
        "datum",
        "Datum",
        FeatureKind.KReference,
        0,
        parameter_ids=("scalar", "extra"),
        definition=Definition,
    )
    Quantity = (
        ParameterValue(CirclePi / 3.0, ValueKind.KAngle, "rad")
        if Method == "angle"
        else ParameterValue(3.0, ValueKind.KLength, "cm")
    )
    Parameters = (
        Parameter("scalar", "Active", Quantity, owner_id="datum"),
        Parameter(
            "extra",
            "Extra",
            ParameterValue(0.0, ValueKind.KLength, "mm"),
            owner_id="datum",
        ),
    )
    Frame = GetDatumFrame(
        Feature, Definition, {Value.id: Value for Value in Parameters}
    )
    return CadDocument(
        CadSource("fixture", "datum", "0" * 64),
        (Configuration("active", "Active", active=True),),
        Parameters,
        (SupportPlane("support", "Probe", Frame),),
        (),
        (),
        (Feature,),
        (),
    )


# native cell and pose evidence move together through the same saved archive graph
def SetSavedDatum(RootValue: Element, Edited: CadDocument, Literal: str) -> None:
    Scalar = RootValue.find(
        "./ObjectData/Object[@name='Parameters']/Properties/Property[@name='cells']/Cells/Cell[@address='B1']"
    )
    Plane = RootValue.find("./ObjectData/Object[@name='Probe']/Properties")
    assert Scalar is not None and Plane is not None
    Scalar.set("content", Literal)
    Placement = Plane.find("./Property[@name='Placement']")
    assert Placement is not None
    Frame = ToData(Edited.support_planes[0].transform)
    assert isinstance(Frame, dict)
    Plane.remove(Placement)
    Plane.append(MakePlacement("Placement", Frame))


# unchanged generated graphs preserve original identities and old static exports still read
def TestDatumSeed() -> None:
    Document = MakeDatumDoc("offset")
    Manifest = DocToManifest(Document)
    EmptySet: set[str] = set()
    for FeatureSet in (None, EmptySet):
        Value = BuildFcstdMut(Manifest, EditableFeatures=FeatureSet)
        with ZipFile(BytesIO(Value)) as Archive:
            RootValue = ParseUntrusted(Archive.read("Document.xml"))
            Members = {
                Information.filename: Information for Information in Archive.infolist()
            }
            assert (
                ReconcileDatum(Document, Manifest, RootValue, Archive, Members)
                is Document
            )
            if FeatureSet:
                RootValue.set("StringHasher", "1")
                RootValue.insert(
                    0,
                    Element(
                        "StringHasher", {"saveall": "0", "threshold": "0", "count": "0"}
                    ),
                )
                assert (
                    ReconcileDatum(Document, Manifest, RootValue, Archive, Members)
                    is Document
                )


# valid edited quantities require the matching native cached placement in both modes
def TestDatumEdit() -> None:
    for Method, Magnitude, Literal in (
        ("offset", -1.25, "=-12.5 mm"),
        ("angle", -CirclePi / 6.0, "=-30 deg"),
    ):
        Document = MakeDatumDoc(Method)
        Scalar, Extra = Document.parameters
        EditedScalar = Replace(Scalar, value=Replace(Scalar.value, value=Magnitude))
        Feature = Document.feature_timeline[0]
        Definition = Feature.definition
        assert isinstance(Definition, BoundDatum)
        Frame = GetDatumFrame(
            Feature, Definition, {"scalar": EditedScalar, "extra": Extra}
        )
        Target = Replace(
            Document,
            parameters=(EditedScalar, Extra),
            support_planes=(Replace(Document.support_planes[0], transform=Frame),),
        )
        Manifest = DocToManifest(Document)
        Value = BuildFcstdMut(Manifest, EditableFeatures=set())
        with ZipFile(BytesIO(Value)) as Archive:
            RootValue = ParseUntrusted(Archive.read("Document.xml"))
            SetSavedDatum(RootValue, Target, Literal)
            Members = {
                Information.filename: Information for Information in Archive.infolist()
            }
            Readback = ReconcileDatum(Document, Manifest, RootValue, Archive, Members)
            assert Readback.support_planes == Target.support_planes
            assert Readback.parameters[0].value == EditedScalar.value
            assert Readback.parameters[0].expression is not None
            assert Readback.parameters[0].expression.language == "freecad"
            assert Readback.feature_timeline == Document.feature_timeline


# pending edits changed aliases and missing bindings cannot return a stale snapshot
def TestDatumGuards() -> None:
    Document = MakeDatumDoc("offset")
    Manifest = DocToManifest(Document)
    Value = BuildFcstdMut(Manifest, EditableFeatures=set())
    with ZipFile(BytesIO(Value)) as Archive:
        XmlValue = Archive.read("Document.xml")
        Members = {
            Information.filename: Information for Information in Archive.infolist()
        }
        for PathValue, Attribute, Changed in (
            ("./Objects/Object[@name='Parameters']", "Touched", "1"),
            (
                "./ObjectData/Object[@name='Probe']/Properties/Property[@name='Placement']/PropertyPlacement",
                "Pz",
                "18",
            ),
            (
                "./ObjectData/Object[@name='Probe']/Properties/Property[@name='ExpressionEngine']/ExpressionEngine/Expression",
                "path",
                "Placement.Base.z",
            ),
            (
                "./ObjectData/Object[@name='Parameters']/Properties/Property[@name='cells']/Cells/Cell[@address='B2']",
                "content",
                "=1 mm",
            ),
            (
                "./ObjectData/Object[@name='Parameters']/Properties/Property[@name='cells']/Cells/Cell[@address='B1']",
                "alias",
                "wrong",
            ),
        ):
            RootValue = ParseUntrusted(XmlValue)
            Found = RootValue.find(PathValue)
            assert Found is not None
            Found.set(Attribute, Changed)
            with Raises(ValueError):
                _ = ReconcileDatum(Document, Manifest, RootValue, Archive, Members)
        RootValue = ParseUntrusted(XmlValue)
        WithShape = {**Members, "added.Shape.brp": ZipInfo("added.Shape.brp")}
        with Raises(ValueError, match="unexpected native data"):
            _ = ReconcileDatum(Document, Manifest, RootValue, Archive, WithShape)
        Props = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties")
        assert Props is not None
        Marker = Props.find(f"./Property[@name='{KDatumBinding}']")
        assert Marker is not None
        Props.remove(Marker)
        Props.set("Count", str(len(Props)))
        with Raises(ValueError, match="binding is missing"):
            _ = ReconcileDatum(Document, Manifest, RootValue, Archive, Members)


# equivalent native unit spelling keeps original source decimal evidence and identities
def TestDatumUnits() -> None:
    Document = MakeDatumDoc("offset")
    Scalar, Extra = Document.parameters
    Original = Replace(Scalar, value=Replace(Scalar.value, value=1.2000000000000002))
    Feature = Document.feature_timeline[0]
    Definition = Feature.definition
    assert isinstance(Definition, BoundDatum)
    Frame = GetDatumFrame(Feature, Definition, {"scalar": Original, "extra": Extra})
    Document = Replace(
        Document,
        parameters=(Original, Extra),
        support_planes=(Replace(Document.support_planes[0], transform=Frame),),
    )
    Manifest = DocToManifest(Document)
    DataValue = BuildFcstdMut(Manifest, EditableFeatures=set())
    with ZipFile(BytesIO(DataValue)) as Archive:
        RootValue = ParseUntrusted(Archive.read("Document.xml"))
        SetSavedDatum(RootValue, Document, "=12 mm")
        Members = {
            Information.filename: Information for Information in Archive.infolist()
        }
        assert (
            ReconcileDatum(Document, Manifest, RootValue, Archive, Members) is Document
        )
