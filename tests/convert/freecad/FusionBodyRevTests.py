# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from tests.convert.freecad.BodyProbe import KBodyProbe
from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from xml.etree.ElementTree import fromstring as ParseXml
from xml.etree.ElementTree import tostring as WriteXml
from zipfile import ZipFile

import pytest as Pytest

from convert import write_document as WriteDocument
from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert.adapters.freecad.EditBodyRev.BodyRevBinding import KBodyRevBinding
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import ReadBodyRev
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from interchange.enums.EnumDocument import Capability
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# each selected rim belongs to an independently editable seed solid
KBodyCases = (
    ("revolveaxes-a83b542c4a07/brep_edge.f3d", "Edge11", 750.0),
    ("revolveaxes-14700158dba9/brep_edge_offset_x.f3d", "Edge9", 1110.0),
)

# the optional executable keeps native recomputation separate from production conversion
KOraclePath = GetFreecadPath()


# native writer binds both feature caches and retains the original neutral edge path
@KRequiresCodec
@Pytest.mark.parametrize(("Capture", "EdgeName", "SeedVolume"), KBodyCases)
def TestLiveBodyRev(
    TmpPath: FilePath, Capture: str, EdgeName: str, SeedVolume: float
) -> None:
    Source = OpenDocument(KStudyPath / Capture, StrictMode=False)
    Output = TmpPath / "linked.FCStd"
    Result = WriteDocument(Source, Output)
    assert (
        Result.application_usable
        and Capability.PARAMETRIC_HISTORY in Result.native_capabilities
    )
    assert Source.bodies[0].topology is not None
    assert Source.bodies[0].topology.volume == Pytest.approx(SeedVolume)
    with ZipFile(Output) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
        (Extrusion,) = RootValue.findall("./Objects/Object[@type='Part::Extrusion']")
        (Revolution,) = RootValue.findall("./Objects/Object[@type='Part::Revolution']")
        SeedName, RevName = Extrusion.attrib["name"], Revolution.attrib["name"]
        AxisLink = RootValue.find(
            f"./ObjectData/Object[@name='{RevName}']/Properties/Property[@name='AxisLink']/LinkSub"
        )
        assert AxisLink is not None and AxisLink.attrib == {
            "value": SeedName,
            "count": "1",
        }
        assert AxisLink[0].attrib == {"value": EdgeName}
        assert any(
            Value.attrib == {"obj": SeedName, "sub": EdgeName}
            for Value in RootValue.findall(
                ".//Property[@name='Selection']/LinkSubList/Link"
            )
        )
        Binding = RootValue.find(
            f"./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='{KBodyRevBinding}']/String"
        )
        assert (
            Binding is not None
            and Binding.get("value") == Source.feature_timeline[-1].id
        )
        assert {
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".Shape.brp")
        } == {
            f"{SeedName}.Shape.brp",
            f"{RevName}.Shape.brp",
        }
    assert OpenDocument(Output) == Source


# a generated solid cannot validate a substituted edge on the same extrusion
@KRequiresCodec
def TestWrongEdge(TmpPath: FilePath) -> None:
    Source = OpenDocument(KStudyPath / KBodyCases[0][0], StrictMode=False)
    Output = TmpPath / "linked.FCStd"
    Wrong = TmpPath / "wrong.FCStd"
    _ = WriteDocument(Source, Output)
    with ZipFile(Output) as Archive, ZipFile(Wrong, "w") as Mutated:
        RootValue = ParseXml(Archive.read("Document.xml"))
        AxisLink = RootValue.find(".//Property[@name='AxisLink']/LinkSub/Sub")
        assert AxisLink is not None and AxisLink.get("value") == "Edge11"
        AxisLink.set("value", "Edge9")
        for Member in Archive.namelist():
            DataValue = (
                WriteXml(RootValue, encoding="utf-8")
                if Member == "Document.xml"
                else Archive.read(Member)
            )
            Mutated.writestr(Member, DataValue)
    with Pytest.raises(FreeCadAdapterA, match="axis"):
        _ = OpenDocument(Wrong)


# native save and reopen retain two solids and the correct phase after signed edits
@KRequiresCodec
@Pytest.mark.skipif(
    not KOraclePath.is_file(), reason="KIT_FREECAD_ORACLE is unavailable"
)
@Pytest.mark.parametrize(("Capture", "EdgeName", "SeedVolume"), KBodyCases)
def TestBodyNative(
    TmpPath: FilePath, Capture: str, EdgeName: str, SeedVolume: float
) -> None:
    Source = OpenDocument(KStudyPath / Capture, StrictMode=False)
    Output = ResolveTemp(TmpPath / "linked.FCStd")
    Saved = ResolveTemp(TmpPath / "linked_saved.FCStd")
    _ = WriteDocument(Source, Output)
    Result = RunProcess(
        [str(KOraclePath), "-c", f"exec({KBodyProbe!r})"],
        env={
            **Environment,
            "KIT_ORACLE_PATH": str(Output),
            "KIT_ORACLE_SAVED": str(Saved),
            "KIT_AXIS_EDGE": EdgeName,
        },
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    Loaded, Rebuilt, Edited, Reopened = (
        tuple(map(float, Value.split()[1:]))
        for Value in Result.stdout.splitlines()
        if Value.startswith("KIT_BODY_REV ")
    )
    assert Loaded[:2] == Pytest.approx((SeedVolume, 2446.25347959525))
    assert Loaded[-1] == Pytest.approx(6.91162991742)
    assert Rebuilt == Pytest.approx(Loaded)
    assert Edited[:2] == Pytest.approx((SeedVolume * 3 / 5, Loaded[1] * 41 / 73))
    assert Edited[-1] < 0
    assert Reopened == Pytest.approx(Edited)
    Readback = OpenDocument(Saved)
    PlanValue = ReadBodyRev(Readback, Readback.feature_timeline[-1])
    assert PlanValue is not None
    assert PlanValue.Extrude.DistanceMm == -3.0 and PlanValue.Revolve.AngleDeg == -41.0
    assert tuple(BodyValue.id for BodyValue in Readback.bodies) == tuple(
        BodyValue.id for BodyValue in Source.bodies
    )
    assert tuple(
        BodyValue.topology.volume for BodyValue in Readback.bodies
    ) == Pytest.approx(Edited[:2])
    ReExport = TmpPath / "readback.FCStd"
    assert WriteDocument(Readback, ReExport).application_usable
    assert OpenDocument(ReExport) == Readback
