from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue

from pytest import mark as TestMark

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import (
    EmitSceneParts,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Links.IsOlderUrn import (
    IsOlderUrn,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Model.Values.GraphicAttr import GraphicAttr
from convert.formats.Fusion.GraphicsCodec.Model.Values.SceneSet import SceneSet

KRoot = FilePath(__file__).resolve().parents[5]

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KBundle = "re/Fusion/examples/.f3z/example1.f3z"


def MemberData(Position: int) -> bytes:
    Bundle = ReadBundle((KRoot / KBundle).read_bytes())
    return Bundle.Documents[Position].DataValue


def AttrName(Value: object) -> str | None:
    if not isinstance(Value, GraphicAttr):
        return None
    return CastValue(GraphicAttr[SceneSet], Value).ClassName


def ClassNames(Value: object) -> set[str]:
    Pending: list[object] = [Value]
    Results: set[str] = set()
    while Pending:
        Current = Pending.pop()
        AttrLabel = AttrName(Current)
        if AttrLabel is not None:
            Results.add(AttrLabel)
        if isinstance(Current, tuple):
            Pending.extend(CastValue(tuple[object, ...], Current))
        elif IsDataClass(Current) and not isinstance(Current, type):
            Pending.extend(
                getattr(Current, Entry.name) for Entry in DataFields(Current)
            )
    return Results


@KRequiresCodec
@TestMark.parametrize(
    "Position, Expected",
    (
        (0, ()),
        (3, ("OverrideTransformAttribute", "OverrideInActivatedVisibilityAttribute")),
        (5, ("FProteinEffectAttribute",)),
        (6, ()),
        (8, ()),
    ),
)
def TestCacheMember(Position: int, Expected: tuple[str, ...]) -> None:
    DataValue = MemberData(Position)
    Model = ReadDocument(DataValue)
    assert Model.Graphics is not None
    assert set(Expected) <= ClassNames(Model.Graphics)
    Original = {
        Entry.Name: Entry.Payload
        for Entry in ReadContainer(DataValue).Parts
        if Entry.Name.startswith("OGS.BlobFolder/")
    }
    Written = {Entry.Name: Entry.Payload for Entry in EmitSceneParts(Model.Graphics)}
    assert Written == Original
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
def TestOldInstance() -> None:
    Model = ReadDocument(MemberData(0))
    assert Model.Graphics is not None
    Versions = dict(Model.Graphics.Globals.Versions)
    assert Versions["F360InstanceNode"] == 0
    assert "GraphicsBlobFeatures" not in Versions


@KRequiresCodec
@TestMark.parametrize("Position", (6, 8))
def TestMeshSlack(Position: int) -> None:
    Model = ReadDocument(MemberData(Position))
    assert Model.Graphics is not None
    Slack = Model.Graphics.MeshSlack + Model.Graphics.FusionSlack
    assert Slack and all(Entry.Payload for Entry in Slack)


def TestOlderUrn() -> None:
    StemValue = "urn:adsk.wipprod:fs.file:vf.Example"
    assert IsOlderUrn(StemValue + "?version=12", StemValue + "?version=11")
    assert not IsOlderUrn(StemValue + "?version=11", StemValue + "?version=12")
    assert not IsOlderUrn(StemValue + "?version=12", StemValue + "?version=12")
    assert not IsOlderUrn(StemValue + "?version=12", StemValue + "Other?version=11")
    assert not IsOlderUrn(StemValue + "?version=12", StemValue + "?version=011")
    assert not IsOlderUrn(StemValue, StemValue + "?version=1")
