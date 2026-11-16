# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import dist as PointDistance

from convert.adapters.Fusion.Native.Circular.RadialBinding import RadialBinding
from convert.adapters.Fusion.Native.Circular.RadialSpecs import KRadialSpecs
from convert.adapters.Fusion.Native.Graph.GraphChecks import RequireFields, SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation


# the neutral parameter and relation must agree with the dimension cache and curve geometry
def ProjectRadial(
    Records: RadialBinding, Feature: NativeNode
) -> tuple[Parameter, SketchRelation]:
    CodeValue, SpecValue = KRadialSpecs[Records.Dimension.ClassName]
    RequireFields(Records.Dimension, {"constraintType": CodeValue})
    SavedInfo = ObjectFields(
        Records.Dimension.Fields[f"{SpecValue.RolePrefix}DimensionInfo"]
    )
    Fields = Records.Parameter.Fields
    Driven = SavedInfo["bDriven"]
    if type(Driven) is not bool or Fields["isDriven"] is not Driven:
        raise ValueError("Native radial dimension and parameter driving modes disagree")
    RequireFields(
        Records.Parameter,
        {
            "isUserDefined": False,
            "isDirty": False,
            "isOrphan": False,
            "expressionType": 0,
            "booleanValue": False,
            "textValue": "",
            "unit": "mm",
            "group": None,
            "rClientObject": None,
        },
    )
    if Fields.get("isExternal", False) is not False:
        raise ValueError("Native radial dimension uses an external parameter")
    NameValue = TextValue(Fields["userName"])
    Expression = ParamExpression(Records.Parameter, {NameValue: Records.Parameter})
    if Expression.parameter_ids or TextValue(SavedInfo["text"]) != Expression.source:
        raise ValueError("Native radial dimension text does not match its literal")
    CheckSizeCircle(SavedInfo, Records, SpecValue.KindValue, SpecValue.Symbol)
    ParameterValueRow = Parameter(
        Records.Parameter.Identity,
        NameValue,
        ParameterValue(NumberValue(Fields["value"]) * 10.0, ValueKind.KLength, "mm"),
        role=ParameterRole.KReference if Driven else ParameterRole.KDriving,
        expression=Expression,
        owner_id=Feature.Identity,
    )
    Relation = SketchRelation(
        Records.Dimension.Identity,
        SpecValue.KindValue,
        (ConstraintRef(Records.Circle.Identity),),
        parameter_id=ParameterValueRow.id,
        driving=not Driven,
    )
    return ParameterValueRow, Relation


# the same full circle must underlie the saved dimension carrier and measurement point
def CheckSizeCircle(
    SavedInfo: dict[str, KEntityValue],
    Records: RadialBinding,
    KindValue: ConstraintKind,
    Symbol: str,
) -> None:
    Carrier = Records.Circle.Fields["arcCurve"]
    ArcFields = ObjectFields(Carrier)
    Center = PointCoords(SavedInfo["centerPoint"])
    Radius = NumberValue(ArcFields["radius"])
    if (
        SavedInfo["arcToDim"] != Carrier
        or Center != PointCoords(ArcFields["center"])
        or SavedInfo["needExtendArcForDim"] is not False
        or SavedInfo["hasTextPoint"] is not True
        or TextValue(SavedInfo["prefix"]) != Symbol
        or Radius <= 0
    ):
        raise ValueError("Native radial dimension has an inconsistent circular carrier")
    Plane = ObjectFields(SavedInfo["plane"])
    Position = PointCoords(SavedInfo["textPosition"])
    Chord = PointCoords(SavedInfo["chordPoint"])
    if (
        Plane["normalReversed"] is not False
        or PointCoords(Plane["origin"]) != (0.0, 0.0, 0.0)
        or PointCoords(Plane["uAxis"]) != (1.0, 0.0, 0.0)
        or PointCoords(Plane["vAxis"]) != (0.0, 1.0, 0.0)
        or Position[2] != 0.0
        or Chord[2] != 0.0
    ):
        raise ValueError("Native radial dimension has inconsistent XY placement")
    Multiplier = 2 if KindValue is ConstraintKind.KDiameter else 1
    Amount = NumberValue(Records.Parameter.Fields["value"])
    SameNumbers(
        (
            NumberValue(SavedInfo["radius"]),
            PointDistance(Center, Chord),
            NumberValue(Records.Binding.Fields["value"]),
            Amount,
        ),
        (Radius, Radius, Amount, Multiplier * Radius),
    )
