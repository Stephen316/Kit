import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.MetaIndex import SegmentKind

known={}
for p in ('DocumentCodec/Vocabulary/DesignClasses.json','ContainerCodec/Assembly/ActClasses.json','ContainerCodec/Browser/BrowserClasses.json'):
 for row in json.loads((ROOT/'src/convert/formats/Fusion'/p).read_bytes()):known[row['ClassGuid'].upper()]=row
reports=[]
for src in ('re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d','re/Fusion/LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d'):
 with ZipFile(ROOT/src) as archive:
  for kind in (SegmentKind.KAct,SegmentKind.KBrowser):
   name='FusionAssetName[Active]/'+kind.value+'1/MetaStream.dat'
   raw=archive.read(name);meta=ReadMetaWire(raw,Segment=kind);diff=[]
   for row in meta.Classes:
    old=known.get(row.ClassGuid.upper())
    if old is None or old['SchemaVersion']!=row.SchemaVersion or old['BaseGuid'].upper()!=row.BaseGuid.upper():
     diff.append({'classGuid':row.ClassGuid,'version':row.SchemaVersion,'base':row.BaseGuid,'ownerCount':len(row.OwnerIds),'qualified':old})
   reports.append({'source':src,'segment':kind.value,'metadataSha256':hashlib.sha256(raw).hexdigest(),'classCount':len(meta.Classes),'differences':diff})
(Path(__file__).with_name('AuxiliarySchemas.json')).write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
