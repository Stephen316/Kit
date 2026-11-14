from dataclasses import replace as ReplaceData
from math import degrees as ToDegrees
from typing import Literal

from convert.adapters.Fusion.Projection.NativeIndex import (
    NativeIndex,
    NativeNumber,
    NativeText,
    StructFields,
)
from convert.adapters.Fusion.Projection.NativeMaterial import NativeMaterial
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


def NativeProfile(Index: NativeIndex, ModelValue: DocumentModel) -> DocumentSpec:
    Params = [Index.Fields[Identity] for Identity in Index.Names.get("Parameter", ())]
    Users = [Value for Value in Params if Value.get("isUserDefined") is True]
    if len(Users) not in (1, 3):
        raise ValueError("Unsupported Fusion user parameter inventory")
    Height = Users[0]
    Title = NativeText(Index.FindOne("FusionComponent")["userName"])
    Result = DocumentSpec(
        Title,
        NativeText(Height["userName"]),
        NativeNumber(Height["value"]) * 10.0,
        "parameter",
        ParamComment=NativeText(Height["comment"]),
    )
    if Index.Names.get("MSketch"):
        Result = SketchProfile(Index, Result)
    if Index.Names.get("DcExtrudeFeature"):
        Tapers = [Value for Value in Params if Value.get("name") == "TaperAngle"]
        if len(Tapers) != 1:
            raise ValueError("Unsupported Fusion taper parameter inventory")
        AngleValue = ToDegrees(NativeNumber(Tapers[0]["value"]))
        KindValue: Literal["cuboid", "frustum", "extrusion"] = (
            "cuboid"
            if Result.ProfileKind == "rectangle"
            else "frustum" if AngleValue else "extrusion"
        )
        Result = ReplaceData(
            Result,
            ProfileKind=KindValue,
            TaperDegrees=AngleValue,
            ExtrusionName=NativeText(
                Index.FindOne("DcExtrudeFeature")["featureUserName"]
            ),
            BodyName=NativeText(Index.FindOne("Body")["userName"]),
            Material=NativeMaterial(ModelValue),
        )
    if len(Users) == 3:
        Result = ReplaceData(
            Result,
            ConstrainRectangle=True,
            WidthParamName=NativeText(Users[1]["userName"]),
            DepthParamName=NativeText(Users[2]["userName"]),
        )
    return Result


def SketchProfile(Index: NativeIndex, SpecValue: DocumentSpec) -> DocumentSpec:
    NameValue = NativeText(Index.FindOne("MSketch")["userName"])
    if Index.Names.get("CircArc3D"):
        ArcValue = StructFields(Index.FindOne("CircArc3D")["arcCurve"])
        return ReplaceData(
            SpecValue,
            ProfileKind="circle",
            RadiusMm=NativeNumber(ArcValue["radius"]) * 10.0,
            SketchName=NameValue,
        )
    Lines = Index.Names.get("Line3D", ())
    if len(Lines) != 4:
        raise ValueError("Unsupported Fusion sketch profile")
    FirstLine = StructFields(Index.Fields[Lines[0]]["lineCurve"])
    NextLine = StructFields(Index.Fields[Lines[1]]["lineCurve"])
    Width = NativeNumber(StructFields(FirstLine["displacement"])["x"]) * 10.0
    Depth = NativeNumber(StructFields(NextLine["displacement"])["y"]) * 10.0
    return ReplaceData(
        SpecValue,
        ProfileKind="rectangle",
        WidthMm=Width,
        DepthMm=Depth,
        SketchName=NameValue,
    )
