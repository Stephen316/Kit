from dataclasses import replace as Replace
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditPlacement import (
    CheckEditFrame,
    ReadEditFrame,
)
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import ReadRuleRows
from convert.adapters.freecad.EditRead.Sketch.SketchGraph import IsSameNode
from convert.adapters.freecad.EditRead.XmlField import (
    EditChild,
    EditFloat,
    OnlyEditChild,
)
from convert.adapters.freecad.EditScale.ScaleSavedGraphState import (
    CheckScaleState,
    CheckExtraProp,
)
from convert.adapters.freecad.Native import IsTransformNear, NativeObject
from interchange.geometry.models.Transform import KOriginZero, KTransformIdentity

# built in property statuses are added when freecad saves the original generated objects
KSavedStatuses = {
    "Label": "134217728",
    "Placement": "8388608",
    "Visibility": "648",
}

# these values require independent solver and cached shape evidence after a rebuild
KLiveFields = {
    "Spreadsheet::Sheet": frozenset({"cells"}),
    "Sketcher::SketchObject": frozenset({"Geometry", "Shape", "InternalShape"}),
    "Part::Extrusion": frozenset({"LengthFwd", "Shape"}),
    "Part::Scale": frozenset({"Shape"}),
}

# the decoded manifest is independently checked before comparison with generated properties
KMetaCarrier = frozenset({"KitManifestData", "KitManifestSHA256"})


# expression paths retain exact generated bindings despite native row ordering
def ReadScaleExprs(Native: NativeObject) -> dict[str, str]:
    Property = Native.properties.get("ExpressionEngine")
    if Property is None:
        return {}
    Engine = OnlyEditChild(Property, "ExpressionEngine")
    Result: dict[str, str] = {}
    if Engine.attrib != {"count": str(len(Engine))} or (Engine.text or "").strip():
        raise ValueError("FreeCAD editable Scale expression count changed")
    for NodeValue in Engine:
        PathValue = NodeValue.get("path", "")
        Expression = NodeValue.get("expression", "")
        if (
            NodeValue.tag != "Expression"
            or len(NodeValue)
            or NodeValue.attrib.keys() != {"path", "expression"}
            or (NodeValue.text or "").strip()
            or not PathValue
            or PathValue in Result
            or not Expression
        ):
            raise ValueError("FreeCAD editable Scale expression row changed")
        if PathValue == "Dir" and Native.type_id == "Part::Extrusion":
            Expression = Expression.replace(" > 1e-07 mm ? ", " > 1e-7 mm ? ")
        Result[PathValue] = Expression
    return Result


# built in displays may gain native status while all dynamic property metadata stays fixed
def CheckScaleAttr(Original: Element, Saved: Element) -> None:
    SavedAttrs = dict(Saved.attrib)
    SourceAttrs = Original.attrib
    Field = SourceAttrs["name"]
    NativeStatus = KSavedStatuses.get(Field)
    if (
        NativeStatus is not None
        and "status" not in SourceAttrs
        and SavedAttrs.get("status") == NativeStatus
    ):
        _ = SavedAttrs.pop("status")
    if SavedAttrs != SourceAttrs or (Saved.text or "").strip():
        raise ValueError(f"FreeCAD editable Scale native {Field} property changed")


# only original expression driven fields may have independently checked numeric edits
def LiveScaleFields(
    Native: NativeObject, Expressions: dict[str, str], IsSeed: bool
) -> frozenset[str]:
    if IsSeed:
        return frozenset()
    Fields = KLiveFields.get(Native.type_id, frozenset())
    if Native.type_id == "Part::Scale":
        return Fields | (frozenset(Expressions) - {"Placement"})
    return Fields


# passive placements keep their original frame while point driven translation stays editable
def CheckScalePose(
    Original: NativeObject,
    Saved: NativeObject,
    Expressions: dict[str, str],
    IsSeed: bool,
) -> None:
    if "Placement" not in Saved.properties:
        return
    Field = "Placement"
    PoseValue = EditChild(Saved, Field, "App::PropertyPlacement", "PropertyPlacement")
    Primary = {"Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3"}
    if (
        len(PoseValue)
        or (PoseValue.text or "").strip()
        or PoseValue.attrib.keys() not in (Primary, Primary | {"A", "Ox", "Oy", "Oz"})
    ):
        raise ValueError("FreeCAD editable Scale native placement is malformed")
    if (
        not IsSeed
        and Field in Expressions
        and Saved.type_id in ("App::Point", "Part::Scale")
    ):
        Frame = ReadEditFrame(Saved, Field)
        Identity = Replace(Frame, origin=KOriginZero)
        if not IsTransformNear(Identity, KTransformIdentity, 1e-9):
            raise ValueError("FreeCAD editable Scale native rotation changed")
        return
    Expected = (
        ReadEditFrame(Original, Field)
        if Field in Original.properties
        else KTransformIdentity
    )
    CheckEditFrame(Saved, Field, Expected)


# property types and passive payloads pin original links identities and solver settings
def CheckSavedProps(Original: NativeObject, Saved: NativeObject, IsSeed: bool) -> None:
    Expected = Original.properties
    Actual = Saved.properties
    Optional: set[str] = (
        {"Placement"} if Saved.type_id == "App::DocumentObjectGroup" else set()
    )
    if Expected.keys() - Optional - Actual.keys():
        raise ValueError(f"FreeCAD editable Scale {Saved.name} lacks a native property")
    Expressions = ReadScaleExprs(Original)
    if ReadScaleExprs(Saved) != Expressions:
        raise ValueError(
            f"FreeCAD editable Scale {Saved.name} expression binding changed"
        )
    Mutable = LiveScaleFields(Original, Expressions, IsSeed)
    for Field, Property in Actual.items():
        Source = Expected.get(Field)
        if Source is None:
            CheckExtraProp(Saved.type_id, Property, Field)
        else:
            CheckScaleAttr(Source, Property)
            CheckSavedValue(Saved, Property, Source, Field, Mutable)
        if Field not in {"Shape", "InternalShape"} and any(
            "file" in NodeValue.attrib for NodeValue in Property.iter()
        ):
            raise ValueError("FreeCAD editable Scale native file routing changed")
    CheckScalePose(Original, Saved, Expressions, IsSeed)
    CheckScaleState(Saved)


# solver rows retain their geometry slots and active state across native save formatting
def CheckSavedValue(
    Native: NativeObject,
    Saved: Element,
    Original: Element,
    Field: str,
    Mutable: frozenset[str],
) -> None:
    if Field in Mutable:
        if Field in {"LengthFwd", "UniformScale", "XScale", "YScale", "ZScale"}:
            FloatValue = OnlyEditChild(Saved, "Float")
            Number = EditFloat(FloatValue, "value")
            if (
                len(FloatValue)
                or FloatValue.attrib.keys() != {"value"}
                or (FloatValue.text or "").strip()
                or Number == 0.0
                or (Field != "LengthFwd" and Number < 0.0)
            ):
                raise ValueError(f"FreeCAD editable Scale native {Field} is invalid")
        return
    if Field in ("ExpressionEngine", "Placement"):
        return
    if Field == "Constraints":
        if any(
            RowValue.Value != RowValue.ExpectedValue
            for RowValue in ReadRuleRows(Native, Original)
        ):
            raise ValueError("FreeCAD editable Scale native constraint value changed")
        return
    if Field == "Label" or (Native.name == "KitMetadata" and Field in KMetaCarrier):
        Value = OnlyEditChild(Saved, "String")
        if len(Value) or Value.attrib.keys() != {"value"} or (Value.text or "").strip():
            raise ValueError(f"FreeCAD editable Scale native {Field} is malformed")
        return
    if len(Saved) != len(Original) or any(
        not IsSameNode(Value, Before)
        for Value, Before in zip(Saved, Original, strict=True)
    ):
        raise ValueError(f"FreeCAD editable Scale {Native.name}.{Field} changed")
