from pathlib import Path
from textwrap import dedent
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'src/convert/formats/Fusion'
P='convert.formats.Fusion.'
def save(path,code):
 p=BASE/(path+'.py');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(dedent(code).lstrip())
def edit(path,old,new):
 p=BASE/(path+'.py');s=p.read_text();assert old in s,path;p.write_text(s.replace(old,new))
save('ContainerCodec/IsGraphicPath','''
from re import fullmatch as FullMatch


def IsGraphicPath(NameValue: str) -> bool:
    return FullMatch(r"OGS\.BlobFolder/OGS/DefaultScene/(world|stream_mesh_[0-9]{3})", NameValue) is not None
''')
save('ContainerCodec/PartDirs','''
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix


def PartDirs(Values: tuple[ContainerPart, ...]) -> set[str]:
    return {
        KAssetPrefix + "/".join(Entry.Name.split("/")[:Index]) + "/"
        for Entry in Values
        for Index in range(1, len(Entry.Name.split("/")))
    }
''')
edit('ContainerCodec/CheckParts','from typing import cast as CastValue','from typing import cast as CastValue\nfrom convert.formats.Fusion.ContainerCodec.IsGraphicPath import IsGraphicPath')
edit('ContainerCodec/CheckParts','len(Sections) != 2\n            or not Sections[1]','(len(Sections) != 2 and (IsPreview or not IsGraphicPath(Entry.Name)))\n            or not Sections[1]')
edit('ContainerCodec/ReadParts','from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive','from convert.formats.Fusion.ArchiveRead.IndexedArchive import IndexedArchive\nfrom convert.formats.Fusion.ContainerCodec.IsGraphicPath import IsGraphicPath')
edit('ContainerCodec/ReadParts','if len(Sections) != 2 or Sections[0] not in KPartFolders:','if (len(Sections) != 2 and not IsGraphicPath(Relative)) or Sections[0] not in KPartFolders:')
edit('ContainerCodec/ContainerRows','from typing import cast as CastValue','from typing import cast as CastValue\nfrom convert.formats.Fusion.ContainerCodec.PartDirs import PartDirs')
edit('ContainerCodec/ContainerRows','    Entries = [ZipAssetRow(Folder, b"", False) for Folder in sorted(Directories)]','    Directories.update(PartDirs(Value.Parts))\n    Entries = [ZipAssetRow(Folder, b"", False) for Folder in sorted(Directories)]')
save('DocumentCodec/Auxiliary/Graphics/ReadSceneParts',f'''
from {P}ContainerCodec.Model.ContainerPart import ContainerPart
from {P}ContainerCodec.IsGraphicPath import IsGraphicPath
from {P}GraphicsCodec.Model.State.GraphicScene import GraphicScene
from {P}GraphicsCodec.Model.State.GraphicsStream import GraphicsStream
from {P}GraphicsCodec.ReadGraphics import ReadGraphics


def ReadSceneParts(Values: tuple[ContainerPart, ...]) -> GraphicScene | None:
    Parts = tuple(Entry for Entry in Values if Entry.Name.startswith("OGS.BlobFolder/"))
    if not Parts:
        return None
    Prefix = "OGS.BlobFolder/OGS/DefaultScene/"
    if any(not IsGraphicPath(Entry.Name) for Entry in Parts):
        raise ValueError("Unsupported Fusion graphics member path")
    WorldParts = tuple(Entry for Entry in Parts if Entry.Name == Prefix + "world")
    if len(WorldParts) != 1:
        raise ValueError("Graphics members require exactly one world")
    Streams = tuple(GraphicsStream(int(Entry.Name[-3:]), Entry.Payload) for Entry in Parts if Entry.Name != Prefix + "world")
    return ReadGraphics(WorldParts[0].Payload, Streams)
''')
save('DocumentCodec/Auxiliary/Graphics/EmitSceneParts',f'''
from {P}ContainerCodec.Model.ContainerPart import ContainerPart
from {P}GraphicsCodec.Model.State.GraphicScene import GraphicScene
from {P}GraphicsCodec.EmitGraphics import EmitGraphics


def EmitSceneParts(Value: GraphicScene | None) -> tuple[ContainerPart, ...]:
    if Value is None:
        return ()
    DataValue = EmitGraphics(Value)
    Prefix = "OGS.BlobFolder/OGS/DefaultScene/"
    return (ContainerPart(Prefix + "world", DataValue.WorldData),) + tuple(ContainerPart(Prefix + f"stream_mesh_{{Entry.StreamIndex:03d}}", Entry.Payload) for Entry in DataValue.MeshStreams)
''')
save('GraphicsCodec/Validation/SceneTargets',f'''
from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from typing import cast as CastValue
from {P}GraphicsCodec.Model.State.GraphicScene import GraphicScene
from {P}GraphicsCodec.Model.Values.EntityRef import EntityRef
from {P}GraphicsCodec.Model.Nodes.NodePayload import NodePayload


def SceneTargets(Value: GraphicScene, ActSegment: int) -> tuple[EntityRef, ...]:
    Pending: list[object] = [Value]
    Results: set[EntityRef] = set()
    while Pending:
        Current = Pending.pop()
        if isinstance(Current, EntityRef):
            Results.add(Current)
        elif isinstance(Current, tuple):
            Pending.extend(CastValue(tuple[object, ...], Current))
        elif IsDataClass(Current) and not isinstance(Current, type):
            Pending.extend(CastValue(object, getattr(Current, Entry.name)) for Entry in DataFields(Current))
            if isinstance(Current, NodePayload) and Current.ActEntity is not None:
                Results.add(EntityRef(ActSegment, Current.ActEntity))
    return tuple(sorted(Results, key=lambda Entry: (Entry.SegmentId, Entry.ObjectId)))
''')
save('DocumentCodec/Auxiliary/Graphics/CheckDocScene',f'''
from {P}DocumentCodec.Model.DocumentModel import DocumentModel
from {P}GraphicsCodec.Validation.SceneTargets import SceneTargets
from {P}MetaIndex import SegmentKind


def CheckDocScene(Value: DocumentModel) -> None:
    if Value.Graphics is None:
        return
    Owners = {{(Segment.Metadata.Header.SegmentId, Record.ObjectId) for Segment in Value.Segments for Record in Segment.Records if Record.IsPrimary}}
    ActIds = tuple(SlotValue.SegmentId for SlotValue in Value.Asset.Segments if SlotValue.Segment == SegmentKind.KAct)
    if len(ActIds) != 1:
        raise ValueError("Graphics entity links require an unambiguous ACT segment")
    Targets = SceneTargets(Value.Graphics, ActIds[0])
    if any((Target.SegmentId, Target.ObjectId) not in Owners for Target in Targets):
        raise ValueError("Graphics references an absent document entity")
''')
for name in ('DocumentParts','DocumentModel'):
 edit('DocumentCodec/Model/'+name,'from dataclasses import dataclass as MakeDataClass','from dataclasses import dataclass as MakeDataClass\nfrom convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene')
 p=BASE/('DocumentCodec/Model/'+name+'.py');s=p.read_text();p.write_text(s+'    Graphics: GraphicScene | None = None\n')
edit('DocumentCodec/Reading/ReadDocParts','from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart','from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart\nfrom convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import ReadSceneParts')
edit('DocumentCodec/Reading/ReadDocParts','    for Value in Values:\n        if Value.Name.startswith("ProteinAssets.BlobParts/"):','    for Value in Values:\n        if Value.Name.startswith("OGS.BlobFolder/"):\n            continue\n        if Value.Name.startswith("ProteinAssets.BlobParts/"):')
edit('DocumentCodec/Reading/ReadDocParts','tuple(Bodies), tuple(Materials), tuple(Snapshots), tuple(Configurations)','tuple(Bodies), tuple(Materials), tuple(Snapshots), tuple(Configurations), ReadSceneParts(Values)')
for name in ('ReadDocument','EmitParsed'):
 edit('DocumentCodec/'+name,'from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel','from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel\nfrom convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.CheckDocScene import CheckDocScene')
edit('DocumentCodec/ReadDocument','        Parts.Configurations,','        Parts.Configurations,\n        Parts.Graphics,')
edit('DocumentCodec/ReadDocument','    CheckDocConfig(Result)','    CheckDocConfig(Result)\n    CheckDocScene(Result)')
edit('DocumentCodec/EmitParsed','    CheckDocConfig(Value)','    CheckDocConfig(Value)\n    CheckDocScene(Value)')
edit('DocumentCodec/EmitParsed','from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer','from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer\nfrom convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import EmitSceneParts')
edit('DocumentCodec/EmitParsed','        + tuple(EmitConfigPart(Configuration) for Configuration in Value.Configurations)','        + tuple(EmitConfigPart(Configuration) for Configuration in Value.Configurations)\n        + EmitSceneParts(Value.Graphics)')
