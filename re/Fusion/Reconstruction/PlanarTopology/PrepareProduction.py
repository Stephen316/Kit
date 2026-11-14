import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import TransformNode
from convert.formats.Fusion.BrepCodec.Journal.PermuteJournal import PermuteJournal
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import ReadPlanarState
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.CreatePolyBody import CreatePolyBody
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.Polyhedron import Polyhedron
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    report=dict(schema='FusionPlanarProductionPreparation/1',scope='Complete source-specific history reconstruction and permutation; separately, standalone source-free convex polyhedra authored from explicit point/face dimensions with a fresh nonidentity affine placement',nativeAcceptance='pending',histories=[],authored=[])
    for label,relative in (('Tetrahedron','re/Fusion/Study/meshconverts-4b42d39fb1d5/faceted_closed.f3d'),('TriangularPipe','re/Fusion/Study/pipemodes-87cfa7d8d82b/triangular.f3d')):
        source=ROOT/relative
        with ZipFile(source) as archive:
            members=tuple(name for name in archive.namelist() if name.endswith('.smbh'))
            if len(members)!=1:raise ValueError('Expected one history')
            member=members[0];payload=archive.read(member);model=ReadJournal(payload)
            order=(0,*reversed(range(1,model.ActiveCount)),*reversed(range(model.ActiveCount,len(model.Entities))))
            for variant,value in (('Production',model),('Permuted',PermuteJournal(model,order))):
                emitted=EmitJournal(value);target=args.output/(label+variant+'.f3d');history=target.with_suffix('.smbh');history.write_bytes(emitted)
                with ZipFile(target,'w',compression=ZIP_DEFLATED) as output:
                    for entry in archive.infolist():output.writestr(entry.filename,emitted if entry.filename==member else archive.read(entry.filename))
                report['histories'].append(dict(label=label,variant=variant,source=str(source),sourceSha256=digest(source),target=str(target),targetSha256=digest(target),member=member,sourceHistorySha256=hashlib.sha256(payload).hexdigest(),historySha256=digest(history),byteExact=emitted==payload,geometry=[asdict(body) for body in ReadPlanarState(value)],states=[state.StateId for state in model.States]))
    stamp=GeometryStamp('Kit semantic planar writer','ASM 232',datetime.now(timezone.utc).strftime('%a %b %d %H:%M:%S %Y'))
    history=HistoryState(4,2,4,1,2)
    tetra=Polyhedron(((0.,0.,0.),(17.,0.,0.),(0.,23.,0.),(0.,0.,31.)),((0,2,1),(0,1,3),(0,3,2),(1,2,3)))
    prism=Polyhedron(((0.,0.,0.),(19.,0.,0.),(0.,13.,0.),(0.,0.,37.),(19.,0.,37.),(0.,13.,37.)),((0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)))
    placed=TransformNode(-1,-1,(0.,1.,0.),(-1.,0.,0.),(0.,0.,1.),(1.1,-.7,.5),1.25,True,False,False)
    for label,spec,placement in (('IndependentTetrahedron',tetra,None),('IndependentTriangularPrism',prism,None),('PlacedTetrahedron',tetra,placed)):
        model=CreatePolyBody(spec,history,stamp,placement);target=args.output/(label+'.smb');target.write_bytes(EmitStateSmb(model));journal=target.with_suffix('.smbh');journal.write_bytes(EmitJournal(model))
        report['authored'].append(dict(label=label,target=str(target),sha256=digest(target),history=str(journal),historySha256=digest(journal),spec=asdict(spec),geometry=[asdict(body) for body in ReadPlanarState(model)],scope='No source archive or payload used for these authored bytes'))
    (args.output/'ProductionPreparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:len(report[key]) for key in ('histories','authored')}))

if __name__=='__main__':main()
