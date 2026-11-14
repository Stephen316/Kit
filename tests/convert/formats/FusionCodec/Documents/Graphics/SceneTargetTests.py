from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as MarkTests, raises as RaisesError

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import (
    EmitSceneParts,
)
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Model.Nodes.GroupValue import GroupValue
from convert.formats.Fusion.GraphicsCodec.Model.Values.EntityRef import EntityRef
from tests.convert.formats.FusionCodec.Documents.Graphics.GraphicsSources import (
    KGraphicSources,
)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestSceneTarget(TmpPath: FilePath) -> None:
    Source = KGraphicSources[0].read_bytes()
    Model = ReadDocument(Source)
    assert Model.Graphics is not None
    Selected = next(
        Entry
        for Entry in Model.Graphics.Objects
        if isinstance(Entry.Value, GroupValue)
        and Entry.Value.NodeData.DataValue is not None
        and Entry.Value.NodeData.DataValue.EntityLink is not None
    )
    assert isinstance(Selected.Value, GroupValue)
    NodeData = Selected.Value.NodeData
    assert NodeData.DataValue is not None
    Invalid = ReplaceValue(NodeData.DataValue, EntityLink=EntityRef(0, 1 << 63))
    Changed = ReplaceValue(
        Selected,
        Value=ReplaceValue(
            Selected.Value, NodeData=ReplaceValue(NodeData, DataValue=Invalid)
        ),
    )
    Objects = tuple(
        Changed if Entry.Reference == Selected.Reference else Entry
        for Entry in Model.Graphics.Objects
    )
    Scene = ReplaceValue(Model.Graphics, Objects=Objects)
    Container = ReadContainer(Source)
    Parts = tuple(
        Entry
        for Entry in Container.Parts
        if not Entry.Name.startswith("OGS.BlobFolder/")
    ) + EmitSceneParts(Scene)
    Target = TmpPath / "DanglingScene.f3d"
    _ = Target.write_bytes(EmitContainer(ReplaceValue(Container, Parts=Parts)))
    with RaisesError(ValueError, match="Graphics references an absent document entity"):
        _ = ReadDocument(Target.read_bytes())
