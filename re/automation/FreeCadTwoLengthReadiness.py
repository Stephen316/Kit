# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Observe current FreeCAD two-length and symmetric readiness via the public SDK."""

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from xml.etree.ElementTree import Element, fromstring
from zipfile import ZipFile

from Corpus import git

# this research command runs against the current checkout's source path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from convert.api.ApiWrite import WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.Records.RecordSource import CadSource

# the same stable identities distinguish end ownership from parameter list order
BOSS_ID = "boss:fresh"
FORWARD_ID = "depth:forward"
REVERSE_ID = "depth:reverse"
TOTAL_ID = "depth:total"


# the roster changes one ownership or end-condition control at a time
@dataclass(frozen=True, slots=True)
class ReadinessCase:
    Name: str
    Forward: float
    Reverse: float | None
    Reorder: bool = False
    OpenOutline: bool = False


# the generated cases use no historical or application source values
CASES = (
    ReadinessCase("two-length", 11.0, 5.0),
    ReadinessCase("two-length-reordered", 11.0, 5.0, Reorder=True),
    ReadinessCase("equal-length", 7.0, 7.0),
    ReadinessCase("equal-length-reordered", 7.0, 7.0, Reorder=True),
    ReadinessCase("symmetric", 16.0, None),
    ReadinessCase("open-outline", 11.0, 5.0, OpenOutline=True),
)


# a closed ordered loop owns four axis and four vertex relations on an identity datum
def BuildSketch(OpenOutline: bool) -> Sketch:
    Points = (
        PlaneVector(0.0, 0.0),
        PlaneVector(37.0, 0.0),
        PlaneVector(37.0, 21.0),
        PlaneVector(0.0, 21.0),
    )
    Edges = tuple(
        SketchEntity(f"edge:{Index}", "line", LineGeometry(Start, End))
        for Index, (Start, End) in enumerate(
            zip(Points, (*Points[1:], Points[0]), strict=True)
        )
    )
    if OpenOutline:
        return Sketch("profile", "Rectangle", "datum:xy", Edges[:-1])
    Ids = tuple(Edge.id for Edge in Edges)
    Axes = tuple(
        SketchRelation(
            f"axis:{Index}", ("horizontal", "vertical")[Index % 2], (ConstraintRef(Id),)
        )
        for Index, Id in enumerate(Ids)
    )
    Vertices = tuple(
        SketchRelation(
            f"corner:{Index}",
            "coincident",
            (ConstraintRef(Previous, "end"), ConstraintRef(Following, "start")),
        )
        for Index, (Previous, Following) in enumerate(
            zip(Ids, (*Ids[1:], Ids[0]), strict=True)
        )
    )
    return Sketch(
        "profile",
        "Rectangle",
        "datum:xy",
        Edges,
        constraints=(*Axes, *Vertices),
        closed_profile_entity_ids=(Ids,),
    )


# each driving record has independent stable identity and the same feature owner
def DepthParameter(Identity: str, Name: str, Millimetres: float) -> Parameter:
    return Parameter(
        Identity,
        Name,
        ParameterValue(Millimetres, ValueKind.KLength, "mm"),
        owner_id=BOSS_ID,
    )


# the fixture retains semantic end ownership beside a permutable parameter roster
def BuildCase(Case: ReadinessCase) -> CadDocument:
    SketchValue = BuildSketch(Case.OpenOutline)
    if Case.Reverse is None:
        Total = DepthParameter(TOTAL_ID, "TotalDepth", Case.Forward)
        Parameters = (Total,)
        Definition = ExtrudeFeature(Total.value, ExtrudeEnd.KMidPlane, symmetric=True)
        Attributes = {}
    else:
        Forward = DepthParameter(FORWARD_ID, "FrontDepth", Case.Forward)
        Reverse = DepthParameter(REVERSE_ID, "BackDepth", Case.Reverse)
        Parameters = (Forward, Reverse)
        Definition = ExtrudeFeature(
            Forward.value,
            ExtrudeEnd.KTwoLengths,
            second_length=Reverse.value,
            second_end_condition=ExtrudeEnd.KBlind,
        )
        Attributes = {"length_parameter_ids": (Forward.id, Reverse.id)}
    if Case.Reorder:
        Parameters = Parameters[::-1]
    Feature = FeatureStep(
        BOSS_ID,
        "RectangularBoss",
        FeatureKind.KExtrusion,
        0,
        sketch_id=SketchValue.id,
        parameter_ids=tuple(Value.id for Value in Parameters),
        operation=BooleanOp.KCreate,
        definition=Definition,
        attributes=Attributes,
    )
    return CadDocument(
        source=CadSource("interchange.json", "fresh-two-length-readiness", ""),
        configurations=(Configuration("config:default", "Default", True),),
        support_planes=(SupportPlane("datum:xy", "XY", Transform()),),
        parameters=Parameters,
        sketches=(SketchValue,),
        selections=(),
        feature_timeline=(Feature,),
        bodies=(DesignBody("body:fresh", "Solid", Feature.id),),
        capabilities=frozenset(
            {Capability.KParamHistory, Capability.KEditableSketches}
        ),
    )


# assertions in a research command remain active in optimized process modes
def Require(Condition: bool, Reason: str) -> None:
    if not Condition:
        raise ValueError(Reason)


# read target-native object properties directly from the emitted document XML
def Properties(Native: Element, Name: str) -> dict[str, Element]:
    (ObjectData,) = (
        Row for Row in Native.findall("./ObjectData/Object") if Row.get("name") == Name
    )
    return {
        Row.attrib["name"]: Row for Row in ObjectData.findall("./Properties/Property")
    }


# scalar properties remain distinct from their live expression dependencies
def PropertyValue(Props: dict[str, Element], Name: str) -> str:
    (Value,) = Props[Name]
    return Value.attrib["value"]


# actual emitted expressions identify which portable cell drives each native property
def ObserveNative(Data: bytes, Case: ReadinessCase) -> dict[str, object]:
    with ZipFile(BytesIO(Data)) as NativeArchive:
        Document = fromstring(NativeArchive.read("Document.xml"))
    Objects = {
        Node.attrib["name"]: Node.attrib["type"]
        for Node in Document.findall("./Objects/Object")
    }
    (Extrusion,) = (Name for Name, Kind in Objects.items() if Kind == "Part::Extrusion")
    (Spreadsheet,) = (
        Name for Name, Kind in Objects.items() if Kind == "Spreadsheet::Sheet"
    )
    Props = Properties(Document, Extrusion)
    Sheet = Properties(Document, Spreadsheet)
    Expressions = {
        Node.attrib["path"]: Node.attrib["expression"]
        for Node in Props["ExpressionEngine"].findall("./ExpressionEngine/Expression")
    }
    Aliases = {
        Node.attrib["alias"]: Node.get("content")
        for Node in Sheet["cells"].findall("./Cells/Cell")
        if Node.get("alias")
    }
    Profile = PropertyValue(Props, "Base")
    Require(
        Objects.get(Profile) == "Sketcher::SketchObject",
        "native extrusion links to its editable sketch",
    )
    Forward = float(PropertyValue(Props, "LengthFwd"))
    Reverse = float(PropertyValue(Props, "LengthRev"))
    Symmetric = PropertyValue(Props, "Symmetric") == "true"
    EndCondition = PropertyValue(Props, "EndCondition")
    Require(
        (Forward, Reverse, Symmetric, EndCondition)
        == (
            Case.Forward,
            Case.Reverse or 0.0,
            Case.Reverse is None,
            "mid_plane" if Case.Reverse is None else "two_lengths",
        ),
        "target stores the exact requested lengths and mode",
    )
    ExpectedDrivers = (
        {"LengthFwd": "Parameters.depth_total"}
        if Case.Reverse is None
        else {
            "LengthFwd": "Parameters.depth_forward",
            "LengthRev": "Parameters.depth_reverse",
        }
    )
    Require(
        set(Aliases)
        == {Expression.split(".")[1] for Expression in ExpectedDrivers.values()},
        "every portable driver has its own target spreadsheet cell",
    )
    return {
        "type": Objects[Extrusion],
        "profile": Profile,
        "spreadsheet_aliases": Aliases,
        "length_fwd": Forward,
        "length_rev": Reverse,
        "symmetric": Symmetric,
        "end_condition": EndCondition,
        "expressions": Expressions,
        "expected_drivers": ExpectedDrivers,
        "missing_drivers": sorted(set(ExpectedDrivers) - set(Expressions)),
        "crossed_drivers": sorted(
            Field
            for Field, Driver in ExpectedDrivers.items()
            if Field in Expressions and Expressions[Field] != Driver
        ),
    }


# the ordinary SDK must receive documented portable input through its real write gate
def ObserveCase(Case: ReadinessCase) -> dict[str, object]:
    Portable = BuildCase(Case).to_json(indent=None)
    Input = CadDocument.from_json(Portable)
    (Feature,) = Input.feature_timeline
    Require(
        tuple(Param.id for Param in Input.parameters) == Feature.parameter_ids
        and all(
            Param.owner_id == Feature.id and Param.role == ParameterRole.KDriving
            for Param in Input.parameters
        ),
        "portable JSON retains each independently driving parameter and owner",
    )
    Observation: dict[str, object] = {
        "portable_sha256": sha256(Portable.encode()).hexdigest(),
        "owner": Feature.id,
        "ordered_parameter_ids": Feature.parameter_ids,
        "end_owner_ids": Feature.attributes.get("length_parameter_ids", (TOTAL_ID,)),
    }
    Output = BytesIO()
    try:
        Result = WriteDocument(
            Input, Output, DestFormat="freecad.fcstd", AllowCarrier=False
        )
    except ValueError as Error:
        Require(not Output.getvalue(), "public SDK published bytes despite refusal")
        return {**Observation, "status": "refused", "reason": str(Error)}
    Data = Output.getvalue()
    Require(
        Result.bytes_written == len(Data) and not Result.carrier_capabilities,
        "public no-carrier output accounting",
    )
    return {
        **Observation,
        "status": "emitted",
        "sdk_reports_application_usable": Result.application_usable,
        "sdk_reports_vendor_loadable": Result.vendor_loadable,
        "native": ObserveNative(Data, Case),
    }


# report binds actual SDK observations to the exact source and fresh neutral payloads
def Report() -> dict[str, object]:
    Require(
        not git(ROOT, "status", "--porcelain", "--untracked-files=all", "--", "src"),
        "readiness observation needs the committed SDK source",
    )
    Result = {Case.Name: ObserveCase(Case) for Case in CASES}
    return {
        "candidate_revision": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "cases": Result,
        "native_accepted": False,
        "replay_sha256": sha256(
            json.dumps(Result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(Report(), sort_keys=True))
