from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditParts import ReadEmptyParts
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.EditProfile import CheckEditPlane
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import (
    CheckEmptyProxy,
    CheckLinkList,
)
from convert.adapters.freecad.EditRead.Revolve.RevGraphLinks import (
    CheckRevCarrier,
    CheckRevConfig,
    CheckRevDeps,
    CheckRevGroup,
    CheckRevPick,
    CheckRevStep,
    RequireRevProp,
)
from convert.adapters.freecad.EditRead.Sketch.SavedSketchFiles import (
    ReadShapeFile,
    ReadSketchFiles,
)
from convert.adapters.freecad.EditRead.XmlField import CheckNoEditExpr, EditScalar
from convert.adapters.freecad.Native import NativeObject
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import KTransformIdentity


# model ownership travels separately from the parsed native angular values
@MakeDataClass(frozen=True, slots=True)
class RevGraph:
    Feature: NativeObject
    Profile: NativeObject
    Sheet: NativeObject
    ShapeEntry: str
    SketchEntry: str
    EmptyEntries: tuple[str, ...]


# named scaffold objects are unique and cannot change their declared role
def RequireRevName(
    Objects: dict[str, NativeObject], NameValue: str, TypeName: str
) -> NativeObject:
    Native = Objects.get(NameValue)
    if Native is None or Native.type_id != TypeName:
        raise ValueError(
            f"FreeCAD editable Revolve native {NameValue} object is missing or changed"
        )
    return Native


# archive names and source caches are bound to their unique native shape owners
def ReadRevFiles(
    Objects: tuple[NativeObject, ...],
    Feature: NativeObject,
    Profile: NativeObject,
    Allowed: set[str],
) -> tuple[str, str, tuple[str, ...]]:
    Shape = ReadShapeFile(Feature, "Shape")
    SketchShape, Internal = ReadSketchFiles(Profile)
    if (
        Shape is None
        or Shape != f"{Feature.name}.Shape.brp"
        or (SketchShape is not None and SketchShape != f"{Profile.name}.Shape.brp")
        or (Internal is not None and Internal != f"{Profile.name}.InternalShape.brp")
    ):
        raise ValueError("FreeCAD editable Revolve shape ownership changed")
    CacheFields = {(Feature.name, "Shape"), (Profile.name, "Shape")}
    EmptyEntries = ReadEmptyParts(Objects, Allowed, CacheFields, "editable Revolve")
    Entries = (
        (Shape, *EmptyEntries)
        if SketchShape is None
        else (Shape, SketchShape, *EmptyEntries)
    )
    if len(set(Entries)) != len(Entries):
        raise ValueError("FreeCAD editable Revolve shape references are ambiguous")
    return Shape, SketchShape or "", EmptyEntries


# verified groups and metadata cannot conceal another independent modeling object
def CheckRevScaf(
    ByName: dict[str, NativeObject],
    Feature: NativeObject,
    ShapeEntry: str,
    Groups: dict[str, tuple[str, ...]],
    Expected: set[str],
) -> None:
    Metadata = RequireRevName(ByName, "KitMetadata", "App::FeaturePython")
    if set(ByName) != Expected | set(Groups) | {Metadata.name}:
        raise ValueError(
            "FreeCAD editable Revolve has an additional or missing native object"
        )
    CheckEmptyProxy(Metadata)
    CheckRevDeps(Metadata, ())
    if "ExpressionEngine" in Metadata.properties:
        CheckNoEditExpr(Metadata)
    for Field, Target in (
        ("FinalFeature", Feature.name),
        ("ExternalLinkTarget", Feature.name),
        ("CachedShapeEntry", ShapeEntry),
    ):
        if EditScalar(Metadata, Field, "App::PropertyString", "String") != Target:
            raise ValueError("FreeCAD editable Revolve native result metadata changed")
    for NameValue, Members in Groups.items():
        CheckRevGroup(ByName[NameValue], Members)


# the exact native dependency graph connects the profile and owned result shape
def ReadRevGraph(
    Objects: tuple[NativeObject, ...],
    DocValue: CadDocument,
    Original: Sketch,
    PlaneValue: SupportPlane,
) -> RevGraph:
    SketchStep, StepValue = DocValue.feature_timeline
    (PickValue,) = DocValue.selections
    ByName = {Value.name: Value for Value in Objects}
    Feature = RequireEditObj(Objects, StepValue.id, "Part::Revolution")
    Profile = RequireEditObj(Objects, Original.id, "Sketcher::SketchObject")
    Plane = RequireEditObj(Objects, PlaneValue.id, "App::Plane")
    Carrier = RequireEditObj(Objects, SketchStep.id, "Part::Feature")
    BodyValue = RequireEditObj(
        Objects, DocValue.bodies[0].id, "App::DocumentObjectGroup"
    )
    AxisPick = RequireRevProp(
        Objects, "KitSelectionId", PickValue.id, "App::FeaturePython"
    )
    Config = RequireRevProp(
        Objects,
        "KitConfigurationId",
        DocValue.configurations[0].id,
        "App::FeaturePython",
    )
    Sheet = RequireRevName(ByName, "Parameters", "Spreadsheet::Sheet")
    CheckRevStep(Feature, StepValue, "feature")
    CheckRevCarrier(Carrier, SketchStep, Profile.name)
    CheckRevPick(AxisPick, PickValue)
    CheckRevConfig(Config)
    CheckEditPlane(Profile, Plane, PlaneValue)
    CheckRevDeps(Plane, ())
    CheckRevDeps(Profile, (Plane.name,))
    CheckRevDeps(Feature, (Profile.name, Sheet.name, AxisPick.name, "Sketches"))
    CheckLinkList(Feature, "Selections", (AxisPick.name,))
    if any(
        EditScalar(ObjectValue, Field, "App::PropertyLink", "Link") != Expected
        for ObjectValue, Field, Expected in (
            (Feature, "Source", Profile.name),
            (Feature, "Sketches", "Sketches"),
            (BodyValue, "Tip", Feature.name),
        )
    ):
        raise ValueError(
            "FreeCAD editable Revolve native source or result link changed"
        )
    CheckEditFrame(BodyValue, "Placement", KTransformIdentity, Optional=True)
    Groups = {
        "SupportPlanes": (Plane.name,),
        "Sketches": (Profile.name,),
        "Selections": (AxisPick.name,),
        "Configurations": (Config.name,),
        "FeatureTimeline": (Carrier.name, Feature.name),
        "Bodies": (BodyValue.name,),
        BodyValue.name: (Profile.name, Carrier.name, Feature.name),
    }
    Expected = {
        Feature.name,
        Profile.name,
        Plane.name,
        Carrier.name,
        AxisPick.name,
        Config.name,
        Sheet.name,
    }
    Shape, SketchShape, EmptyEntries = ReadRevFiles(Objects, Feature, Profile, Expected)
    CheckRevScaf(ByName, Feature, Shape, Groups, Expected)
    return RevGraph(Feature, Profile, Sheet, Shape, SketchShape, EmptyEntries)
