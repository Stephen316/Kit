from collections.abc import Mapping
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditObjects import FindEditObject, RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.EditExtrusion import CheckEditMaker
from convert.adapters.freecad.EditRead.EditProfile import CheckEditPlane
from convert.adapters.freecad.EditRead.EditSheet import EditCells
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import ReadRuleRows
from convert.adapters.freecad.EditRead.Sketch.SavedSketchGeom import ReadSketchGeom
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import (
    CheckExtensions,
    CheckSketchOpts,
)
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat, EditScalar
from convert.adapters.freecad.InlineRead.ReadInline import (
    ReadExpected,
    ReadInlineDepth,
    ReadInlineExpr,
    ReadInlineScope,
    IsInlineCell,
)
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.Sketch import Sketch


# exact scalar and flag agreement is required even when the embedded graph still validates
def GuardEndFields(Current: NativeObject, Expected: NativeObject) -> None:
    for FieldName in ("LengthFwd", "LengthRev"):
        if ReadInlineDepth(Current, FieldName) != ReadInlineDepth(Expected, FieldName):
            raise ValueError(f"inline {FieldName} differs from the embedded source")
    for FieldName, TypeName, ChildName in (
        ("Solid", "App::PropertyBool", "Bool"),
        ("Reversed", "App::PropertyBool", "Bool"),
        ("Symmetric", "App::PropertyBool", "Bool"),
        ("Suppressed", "App::PropertyBool", "Bool"),
        ("DirMode", "App::PropertyEnumeration", "Integer"),
        ("EndCondition", "App::PropertyString", "String"),
    ):
        if EditScalar(Current, FieldName, TypeName, ChildName) != EditScalar(
            Expected, FieldName, TypeName, ChildName
        ):
            raise ValueError(f"inline {FieldName} differs from the embedded source")
    Before = EditChild(Expected, "Dir", "App::PropertyVector", "PropertyVector")
    After = EditChild(Current, "Dir", "App::PropertyVector", "PropertyVector")
    if any(
        EditFloat(Before, FieldName) != EditFloat(After, FieldName)
        for FieldName in ("valueX", "valueY", "valueZ")
    ):
        raise ValueError("inline direction differs from the embedded source")
    CheckEditFrame(Current, "Placement", Transform(), Optional=True)
    CheckEditMaker(Current)
    for FieldName in ("TaperAngle", "TaperAngleRev"):
        if (
            FieldName in Current.properties
            and EditFloat(
                EditChild(Current, FieldName, "App::PropertyAngle", "Float"), "value"
            )
            != 0.0
        ):
            raise ValueError("inline taper differs from the supported source")


# parameter aliases and end paths must still describe the original owned roster
def GuardEndCells(
    Current: NativeObject,
    Expected: NativeObject,
    Objects: tuple[NativeObject, ...],
    Before: tuple[NativeObject, ...],
) -> None:
    Expressions = ReadInlineExpr(Expected)
    if ReadInlineExpr(Current) != Expressions:
        raise ValueError(
            "inline end expression bindings differ from the embedded source"
        )
    (Original,) = (Value for Value in Before if Value.type_id == "Spreadsheet::Sheet")
    (Saved,) = (Value for Value in Objects if Value.type_id == "Spreadsheet::Sheet")
    if Saved.name != Original.name:
        raise ValueError("inline parameter sheet owner changed")
    OriginalCells, SavedCells = EditCells(Original, True), EditCells(Saved, True)
    if set(OriginalCells) != set(SavedCells):
        raise ValueError("inline parameter alias roster changed")
    Owned = {
        Source.removeprefix(Original.name + "."): ReadInlineDepth(Expected, FieldName)
        for FieldName, Source in Expressions.items()
        if Source.startswith(Original.name + ".")
    }
    if len(Owned) != len(Expressions):
        raise ValueError(
            "inline parameter expression is outside the direct alias scope"
        )
    for Alias, CellValue in SavedCells.items():
        if not IsInlineCell(
            EditScalarCell(OriginalCells[Alias]),
            EditScalarCell(CellValue),
            Owned.get(Alias),
        ):
            raise ValueError(
                f"inline parameter alias {Alias} differs from the embedded source"
            )


# missing contents cannot silently become an unchanged empty parameter
def EditScalarCell(CellValue: Element) -> str:
    Content = CellValue.get("content")
    if Content is None:
        raise ValueError("inline parameter cell content is missing")
    return Content


# every source collection must fit the actual validated native inventory before expected emission
def GuardInventory(Document: CadDocument, Objects: tuple[NativeObject, ...]) -> None:
    if len(Document.support_planes) != sum(
        Value.type_id == "App::Plane" for Value in Objects
    ):
        raise ValueError("inline plane owner inventory changed")
    if len(Document.sketches) != sum(
        Value.type_id == "Sketcher::SketchObject" for Value in Objects
    ):
        raise ValueError("inline sketch owner inventory changed")
    (Sheet,) = (Value for Value in Objects if Value.type_id == "Spreadsheet::Sheet")
    if len(Document.parameters) != len(EditCells(Sheet, True)):
        raise ValueError("inline parameter inventory changed")


# new geometric objects cannot be hidden behind an unchanged original feature and body tip
def ReadShapeOwners(Objects: tuple[NativeObject, ...]) -> set[tuple[str, str]]:
    return {
        (Value.name, Value.type_id)
        for Value in Objects
        if Value.type_id.startswith(("Part::", "PartDesign::", "Sketcher::"))
        or any(
            Property.get("type") == "Part::PropertyPartShape"
            for Property in Value.properties.values()
        )
    }


# native geometry construction and solver records must remain the original source profile
def GuardProfile(
    Current: NativeObject, Expected: NativeObject, Original: Sketch
) -> None:
    CheckExtensions(Current)
    CheckSketchOpts(Current)
    if ReadSketchGeom(Current, Original) is not Original:
        raise ValueError(
            "inline native profile geometry differs from the embedded source"
        )
    Rules = Expected.properties.get("Constraints")
    if Rules is None:
        raise ValueError("inline source constraints are unavailable")
    if any(
        RowValue.Value != RowValue.ExpectedValue
        for RowValue in ReadRuleRows(Current, Rules)
    ):
        raise ValueError(
            "inline native constraint value differs from the embedded source"
        )


# unique kit identities bind the native base and body tip to the same original feature graph
def GuardOwners(
    Document: CadDocument,
    Feature: FeatureStep,
    Objects: tuple[NativeObject, ...],
    Before: tuple[NativeObject, ...],
) -> None:
    Current = RequireEditObj(Objects, Feature.id, "Part::Extrusion")
    Expected = RequireEditObj(Before, Feature.id, "Part::Extrusion")
    if sum(Value.type_id == "Part::Extrusion" for Value in Objects) != 1:
        raise ValueError("inline extrusion owner roster changed")
    (Sketch,) = (Value for Value in Document.sketches if Value.id == Feature.sketch_id)
    (Plane,) = (
        Value
        for Value in Document.support_planes
        if Value.id == Sketch.support_plane_id
    )
    NativeSketch = RequireEditObj(Objects, Sketch.id, "Sketcher::SketchObject")
    ExpectedSketch = RequireEditObj(Before, Sketch.id, "Sketcher::SketchObject")
    NativePlane = RequireEditObj(Objects, Plane.id, "App::Plane")
    if EditScalar(Current, "Base", "App::PropertyLink", "Link") != NativeSketch.name:
        raise ValueError("inline native base no longer owns the original sketch")
    ExpectedBody = FindEditObject(Before, Document.bodies[0].id)
    if ExpectedBody is None:
        raise ValueError("inline source body owner is missing")
    BodyValue = RequireEditObj(Objects, Document.bodies[0].id, ExpectedBody.type_id)
    if EditScalar(BodyValue, "Tip", "App::PropertyLink", "Link") != Current.name:
        raise ValueError("inline native body tip changed")
    CheckEditPlane(NativeSketch, NativePlane, Plane)
    GuardProfile(NativeSketch, ExpectedSketch, Sketch)
    GuardEndFields(Current, Expected)
    GuardEndCells(Current, Expected, Objects, Before)


# unproven edits must refuse rather than silently substitute the original neutral snapshot
def GuardInline(
    Document: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    *,
    RetainedRoute: bool,
) -> None:
    if RetainedRoute:
        return
    try:
        Feature = ReadInlineScope(Document, Manifest)
        if Feature is None:
            return
        Objects = ParseObjects(RootValue)
        GuardInventory(Document, Objects)
        Before = ReadExpected(Manifest)
        if ReadShapeOwners(Objects) != ReadShapeOwners(Before):
            raise ValueError("inline native geometry owner inventory changed")
        GuardOwners(Document, Feature, Objects, Before)
    except (ValueError, KeyError, TypeError, OverflowError) as Problem:
        raise ValueError(
            "FreeCAD inline native controls require unsupported edit reconciliation: "
            + str(Problem)
        ) from Problem
