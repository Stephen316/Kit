import json,sys,hashlib
from pathlib import Path
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'src'))
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from convert.formats.Fusion.DocumentCodec.Reading.ReadDocParts import ReadDocParts
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
sources=('re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d','re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d')
reports=[]
for source in sources:
 raw=(ROOT/source).read_bytes();container=ReadContainer(raw);schemas=ReadDocSchemas();metadata=tuple(ReadMetaWire(s.Metadata,Segment=k.Segment) for s,k in zip(container.Streams,container.Asset.Segments));segments=tuple(ReadDocSegment(s,m,MakeDocProfile(schemas,metadata,s.SegmentId)) for s,m in zip(container.Streams,metadata));parts=ReadDocParts(tuple(p for p in container.Parts if not p.Name.startswith("OGS.BlobFolder/")))
 refs=[]
 for seg in segments:
  for record in seg.Records:
   for group in record.Groups:
    for field in group.Fields:
     if field.FieldName in ('physicalMaterial','visualMaterial') and field.Value is not None:refs.append({'record':record.ObjectId,'class':group.ClassGuid,'field':field.FieldName,'value':asdict(field.Value)})
 assets=[]
 for part in parts.Materials:
  for asset in part.Package.Assets:
   assets.append({'package':part.Name,'instance':asset.InstanceId,'definition':asset.DefinitionId,'role':asset.AssetRole,'fields':[asdict(p) for p in asset.Properties if asset.DefinitionId == 'Generic' or p.FieldName in ('AssetLibID','AssetID','AssetType','Name','UIName')],'definitions':[asdict(p) for p in asset.Definitions if asset.DefinitionId == 'Generic' or p.FieldName in ('AssetLibID','AssetID','AssetType','Name','UIName')]})
 reports.append({'source':source,'sha256':hashlib.sha256(raw).hexdigest(),'refs':refs,'assets':assets})
Path(__file__).with_name('NativeMaterialLinks.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
