# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from collections.abc import Mapping
from dataclasses import replace as Replace

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import ReadEditFrame
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditScalar
from convert.adapters.freecad.EditScale.ScaleSavedParams import (
    ReadScaleCells,
    ReadScaleScalar,
)
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Formula.FormulaUnits import GetQuantity
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.validation.BoundPlaneValidate import CheckBoundPlane
from interchange.features.BoundPlaneValues import GetDatumFrame
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Transform import Transform
from interchange.records.RecordParameter import Parameter


# native saves can round equivalent canonical quantities to fifteen significant digits
def IsSameDatumQty(Original: Parameter, Updated: Parameter) -> bool:
    Before = GetQuantity(Original.value)
    After = GetQuantity(Updated.value)
    return (
        Before is not None
        and After is not None
        and Before[1] == After[1]
        and (
            Before[0] == After[0]
            or format(Before[0], ".15g") == format(After[0], ".15g")
        )
    )


# only the original active scalar can drive a saved edit
def ReadDatumParams(
    Document: CadDocument,
    Manifest: Mapping[str, object],
    Native: NativeObject,
    Expected: NativeObject,
    Editable: set[str],
) -> tuple[Parameter, ...]:
    Catalog = ParamCatalog(Items(Manifest.get("parameters", [])))
    Cells = ReadScaleCells(Native, Catalog)
    Original = ReadScaleCells(Expected, Catalog)
    Result: list[Parameter] = []
    for Param in Document.parameters:
        Alias = Catalog.Aliases[Param.id]
        Before = Original[Alias].get("content", "")
        After = Cells[Alias].get("content", "")
        if After != Before:
            try:
                Updated = ReadScaleScalar(Param, After)
            except ValueError as ErrorInfo:
                raise ValueError(
                    "FreeCAD editable datum cell is not a compatible literal"
                ) from ErrorInfo
            if not IsSameDatumQty(Param, Updated):
                if Param.id not in Editable:
                    raise ValueError(
                        "FreeCAD editable datum has an inactive parameter edit"
                    )
                if Updated.expression is None:
                    raise ValueError(
                        "FreeCAD editable datum cell has no literal expression"
                    )
                Param = Replace(
                    Updated,
                    expression=Replace(Updated.expression, language="freecad"),
                )
        Result.append(Param)
    return tuple(Result)


# native placement serialization must retain exactly the two supported rotation witnesses
def ReadDatumPose(Native: NativeObject) -> Transform:
    Value = EditChild(
        Native, "Placement", "App::PropertyPlacement", "PropertyPlacement"
    )
    Primary = {"Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3"}
    if (
        len(Value)
        or (Value.text or "").strip()
        or Value.attrib.keys()
        not in (
            Primary,
            Primary | {"A", "Ox", "Oy", "Oz"},
        )
    ):
        raise ValueError("FreeCAD editable datum native placement is malformed")
    return ReadEditFrame(Native, "Placement")


# the exact source frame and native placement must agree independently of the sheet
def ApplyDatumVals(
    Document: CadDocument,
    Controls: tuple[tuple[FeatureStep, BoundDatum], ...],
    Native: dict[str, NativeObject],
    Parameters: tuple[Parameter, ...],
) -> CadDocument:
    Before = {Value.id: Value for Value in Document.parameters}
    Params = {Value.id: Value for Value in Parameters}
    PlaneFrames = {Value.id: Value for Value in Document.support_planes}
    Objects = tuple(Native.values())
    for StepValue, Definition in Controls:
        Plane = PlaneFrames[Definition.SupportPlaneId]
        Owner = RequireEditObj(Objects, Plane.id, "App::Plane")
        if (
            EditScalar(Owner, "KitFeatureId", "App::PropertyString", "String")
            != StepValue.id
        ):
            raise ValueError("FreeCAD editable datum native feature identity changed")
        Witness = Replace(Plane, transform=ReadDatumPose(Owner))
        CheckBoundPlane(StepValue, Definition, Params, {Plane.id: Witness})
        Identity = Definition.ScalarParameterId
        if Params[Identity] != Before[Identity]:
            Derived = GetDatumFrame(StepValue, Definition, Params)
            PlaneFrames[Plane.id] = Replace(Plane, transform=Derived)
    if Parameters == Document.parameters:
        return Document
    Result = Replace(
        Document,
        parameters=Parameters,
        support_planes=tuple(
            PlaneFrames[Value.id] for Value in Document.support_planes
        ),
    )
    Result.assert_valid()
    return Result
