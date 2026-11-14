from collections.abc import Callable
from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import mark as TestMark, raises as ExpectRaises

from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import (
    EmitSceneParts,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import (
    ReadSceneParts,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedEdge import (
    EnhancedEdge,
)
from convert.formats.Fusion.GraphicsCodec.Model.Values.EnhancedFace import (
    EnhancedFace,
)

KRoot = FilePath(__file__).resolve().parents[5]

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KReencoded = (".protein", ".smb", ".smbh")

KScenePath = "FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/"

KDocuments = (
    "re/Fusion/Study/timeline-5867579925b5/grouped.f3d",
    "re/Fusion/Study/timeline-5867579925b5/reordered_b.f3d",
    "re/Fusion/Study/timeline-5867579925b5/rolled_back.f3d",
    "re/Fusion/Study/timeline-5867579925b5/suppressed_b.f3d",
    "re/Fusion/Study/timeline-72406b67a839/reordered_b.f3d",
    "re/Fusion/Study/timeline-72406b67a839/suppressed_b.f3d",
    "re/Fusion/Study/timeline-expanded-2396e32f2574/expanded.f3d",
    "re/Fusion/Study/timeline-fee448f6a592/suppressed_b.f3d",
    "re/Fusion/LocalOracle/RolledHistory/RolledHistoryReemitted.f3d",
)

KBundles = (
    "re/Fusion/examples/.f3z/example1.f3z",
    "re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z",
)

KSceneMembers = (3, 5, 8)


def ReadMembers(DataValue: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(DataValue)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


def LoadBytes(PathName: str) -> bytes:
    return (KRoot / PathName).read_bytes()


def BundleScene(Position: int) -> bytes:
    Bundle = ReadBundle(LoadBytes(KBundles[0]))
    Documents = sorted(
        (Entry.FileName, Entry.DataValue)
        for Entry in Bundle.Documents
        if Entry.FileName.lower().endswith(".f3d")
    )
    return Documents[Position][1]


def SwapItems(
    Value: object, ItemKind: type[object], Change: Callable[[object], object]
) -> object:
    if isinstance(Value, ItemKind):
        return Change(Value)
    if isinstance(Value, tuple):
        return tuple(
            SwapItems(Entry, ItemKind, Change)
            for Entry in CastValue(tuple[object, ...], Value)
        )
    if IsDataClass(Value) and not isinstance(Value, type):
        return Replace(
            Value,
            **{
                FieldInfo.name: SwapItems(
                    getattr(Value, FieldInfo.name), ItemKind, Change
                )
                for FieldInfo in DataFields(Value)
                if FieldInfo.init
            },
        )
    return Value


def CountItems(Value: object, ItemKind: type[object]) -> int:
    if isinstance(Value, ItemKind):
        return 1
    if isinstance(Value, tuple):
        return sum(
            CountItems(Entry, ItemKind)
            for Entry in CastValue(tuple[object, ...], Value)
        )
    if IsDataClass(Value) and not isinstance(Value, type):
        return sum(
            CountItems(getattr(Value, FieldInfo.name), ItemKind)
            for FieldInfo in DataFields(Value)
        )
    return 0


def DropNormal(Value: object) -> object:
    Current = CastValue(EnhancedEdge, Value)
    return Replace(Current, Normals=Current.Normals[:-1])


def DangleEdge(Value: object) -> object:
    Current = CastValue(EnhancedFace, Value)
    return Replace(Current, EdgeIds=(65536,))


@KRequiresCodec
@TestMark.parametrize("PathName", KDocuments)
def TestSceneReplay(PathName: str) -> None:
    Source = LoadBytes(PathName)
    Model = ReadDocument(Source)
    Output = EmitParsed(Model)
    assert ReadDocument(Output) == Model
    Before, After = ReadMembers(Source), ReadMembers(Output)
    assert set(Before) == set(After)
    assert KScenePath + "Fusion_mesh_000" in Before
    Changed = {
        Entry
        for Entry in Before
        if Before[Entry] != After[Entry] and not Entry.endswith(KReencoded)
    }
    assert not Changed
    assert CountItems(Model, EnhancedEdge) > 0
    assert CountItems(Model, EnhancedFace) > 0


@KRequiresCodec
@TestMark.parametrize("Position", KSceneMembers)
def TestSceneParts(Position: int) -> None:
    Container = ReadContainer(BundleScene(Position))
    Scene = ReadSceneParts(Container.Parts)
    Emitted = EmitSceneParts(Scene)
    Original = {
        Entry.Name: Entry.Payload
        for Entry in Container.Parts
        if Entry.Name.startswith("OGS.BlobFolder/")
    }
    assert {Entry.Name: Entry.Payload for Entry in Emitted} == Original
    assert ReadSceneParts(Emitted) == Scene


@KRequiresCodec
def TestWindowsIds() -> None:
    Container = ReadContainer(LoadBytes("re/Fusion/examples/.f3d/example2.f3d"))
    Scene = ReadSceneParts(Container.Parts)
    Emitted = EmitSceneParts(Scene)
    Original = {
        Entry.Name: Entry.Payload
        for Entry in Container.Parts
        if Entry.Name.startswith("OGS.BlobFolder/")
    }
    assert {Entry.Name: Entry.Payload for Entry in Emitted} == Original
    assert ReadSceneParts(Emitted) == Scene


@KRequiresCodec
@TestMark.parametrize("PathName", KBundles)
def TestBundles(PathName: str) -> None:
    Bundle = ReadBundle(LoadBytes(PathName))
    assert ReadBundle(EmitBundle(Bundle)) == Bundle


@KRequiresCodec
def TestEdgeReject() -> None:
    Model = ReadDocument(LoadBytes(KDocuments[0]))
    Broken = SwapItems(Model, EnhancedEdge, DropNormal)
    with ExpectRaises(ValueError, match="enhanced edge layout"):
        _ = EmitParsed(CastValue(DocumentModel, Broken))


@KRequiresCodec
def TestFaceReject() -> None:
    Model = ReadDocument(LoadBytes(KDocuments[0]))
    Broken = SwapItems(Model, EnhancedFace, DangleEdge)
    with ExpectRaises(ValueError, match="enhanced display item references"):
        _ = EmitParsed(CastValue(DocumentModel, Broken))
