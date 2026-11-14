import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Round.CreateRoundBody import CreateRoundBody
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereBody import SphereBody
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusBody import TorusBody
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed

OUT=ROOT/'re/Fusion/LocalOracle/RoundBodies'
HISTORY=HistoryState(7,2,7,1,2,7)
CONTROLS=('Sphere','Torus','TiltedTorus','PlacedTorus')
TRIMMED=(('PartialClosed','Study/pipemodes-87cfa7d8d82b/partial_closed.f3d'),('CompositeCircular','Study/pipepaths-3d11bd427946/composite_circular.f3d'),('RoundFillets','Study/specialfillets-d50f7a4f04e0/rule_all_rounds.f3d'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare_standalone(report):
    stamp=GeometryStamp('Kit independent analytic author','ASM 232.5.0.65535 OSX',datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))
    models=(('AuthoredSphere',SphereBody(19.0,(-11.0,7.0,13.0))),('AuthoredTorus',TorusBody(31.0,9.0,(17.0,-13.0,5.0))),('AuthoredTilted',TorusBody(31.0,9.0,(17.0,-13.0,5.0),(0.0,0.6,0.8))))
    for label,model in models:
        journal=CreateRoundBody(model,HISTORY,stamp)
        payload=EmitStateSmb(journal)
        target=OUT/(label+'.smb');target.write_bytes(payload)
        history=OUT/(label+'.smbh');history.write_bytes(EmitJournal(journal))
        center=[value/10 for value in model.CenterMm]
        if isinstance(model,SphereBody):
            radius=model.RadiusMm/10
            volume=4*math.pi*radius**3/3;area=4*math.pi*radius**2;extents=[radius]*3
        else:
            major,minor=model.MajorRadiusMm/10,model.MinorRadiusMm/10
            volume=2*math.pi**2*major*minor**2;area=4*math.pi**2*major*minor
            extents=[major*math.sqrt(max(0.0,1-axis*axis))+minor for axis in model.AxisVector]
        report['standalone'].append(dict(label=label,target=str(target.relative_to(ROOT)),targetSha256=digest(payload),history=str(history.relative_to(ROOT)),historySha256=digest(history.read_bytes()),input=asdict(model),expected=dict(faces=1,edges=0,vertices=0,volumeCm3=volume,areaCm2=area,centerCm=center,boundsCm=[[coordinate-extent for coordinate,extent in zip(center,extents)],[coordinate+extent for coordinate,extent in zip(center,extents)]])))
        print(label,digest(payload),flush=True)


def prepare_controls(report):
    for label in CONTROLS:
        source=ROOT/'re/Fusion/LocalOracle/RoundCarriers'/(label+'.f3d')
        with ZipFile(source) as archive:
            member=next(name for name in archive.namelist() if name.endswith('.smb'))
            original=archive.read(member)
        model=ReadGeometry(original);payload=EmitGeometry(model)
        target=OUT/('Decoded'+label+'.smb');target.write_bytes(payload)
        report['geometry'].append(dict(label=label,source=str(source.relative_to(ROOT)),sourceSha256=digest(source.read_bytes()),member=member,geometrySha256=digest(original),target=str(target.relative_to(ROOT)),targetSha256=digest(payload),entityCount=len(model.Entities),byteExact=payload==original))
        print('Decoded'+label,digest(payload),flush=True)


def prepare_histories(report):
    for label,relative in TRIMMED:
        source=ROOT/'re/Fusion'/relative
        with ZipFile(source) as archive:
            member=next(name for name in archive.namelist() if name.endswith('.smbh'))
            original=archive.read(member)
            model=ReadJournal(original);payload=EmitJournal(model)
            target=OUT/(label+'History.f3d')
            with ZipFile(target,'w') as output:
                for entry in archive.infolist():
                    output.writestr(entry.filename,payload if entry.filename==member else archive.read(entry))
        report['histories'].append(dict(label=label,source=str(source.relative_to(ROOT)),sourceSha256=digest(source.read_bytes()),member=member,historySha256=digest(original),target=str(target.relative_to(ROOT)),targetSha256=digest(target.read_bytes()),emittedHistorySha256=digest(payload),activeRecords=model.ActiveCount,allRecords=len(model.Entities),states=len(model.States),byteExact=payload==original,boundary='Typed complete history replacement; preserves this source archive own other members'))
        print(label,digest(payload),flush=True)


def prepare_documents(report):
    sources=tuple((label,'LocalOracle/RoundCarriers/'+label+'.f3d') for label in CONTROLS)+TRIMMED
    for label,relative in sources:
        source=ROOT/'re/Fusion'/relative
        model=ReadDocument(source.read_bytes());payload=EmitParsed(model)
        target=OUT/(label+'Document.f3d');target.write_bytes(payload)
        report['documents'].append(dict(label=label,source=str(source.relative_to(ROOT)),sourceSha256=digest(source.read_bytes()),target=str(target.relative_to(ROOT)),targetSha256=digest(payload),segments=len(model.Segments),histories=len(model.Bodies),snapshots=len(model.Snapshots),boundary='Entire archive reconstructed through public typed ReadDocument and EmitParsed'))
        print(label+'Document',digest(payload),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=('standalone','geometry','histories','documents','all'),default='all');options=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    report=dict(schema='FusionRoundBodyPreparation/1',status='preparing',standalone=[],geometry=[],histories=[],documents=[])
    for name,action in (('standalone',prepare_standalone),('geometry',prepare_controls),('histories',prepare_histories),('documents',prepare_documents)):
        if options.kind in (name,'all'):
            action(report)
            (OUT/('Preparation'+options.kind.title()+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    report['status']='prepared'
    (OUT/('Preparation'+options.kind.title()+'.json')).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
