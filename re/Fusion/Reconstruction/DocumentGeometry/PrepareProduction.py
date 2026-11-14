import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile
import io

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'src'))
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed

OUT = ROOT/'re/Fusion/LocalOracle/DocumentGeometry'
SOURCES = (
    ('BaseClosed','Study/meshconvertoperations-5af73924aa60/base_feature_closed.f3d'),
    ('BaseOpen','Study/meshconvertoperations-5af73924aa60/base_feature_open.f3d'),
    ('TwoBodies','Study/meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d'),
    ('FacetedClosed','Study/meshconverts-4b42d39fb1d5/faceted_closed.f3d'),
    ('FacetedOpen','Study/meshconverts-4b42d39fb1d5/faceted_open.f3d'),
    ('TriangularPipe','Study/pipemodes-87cfa7d8d82b/triangular.f3d'),
    ('NativeCircle','LocalOracle/PublicAdapter/vendor_circleEdited.f3d'),
    ('NativeCylinder','LocalOracle/PublicAdapter/vendor_extrusionEdited.f3d'),
    ('NativeFrustum','LocalOracle/PublicAdapter/vendor_frustumEdited.f3d'),
)


def hashes(payload):
    with ZipFile(io.BytesIO(payload)) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if not name.endswith('/')}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='*')
    parser.add_argument('--output',type=Path,default=OUT)
    options=parser.parse_args()
    output=ROOT/options.output
    output.mkdir(parents=True,exist_ok=True)
    report=dict(schema='FusionTypedGeometryDocumentPreparation/1',status='preparing',boundary='Complete public ReadDocument to EmitParsed; all non-preview members reconstructed from typed semantic models. No archive member copying or native runtime.',cases=[])
    for label,relative in SOURCES:
        if options.only and label not in options.only:
            continue
        source=ROOT/'re/Fusion'/relative
        original=source.read_bytes()
        model=ReadDocument(original)
        encoded=EmitParsed(model)
        target=output/(label+'.f3d')
        target.write_bytes(encoded)
        before,after=hashes(original),hashes(encoded)
        report['cases'].append(dict(label=label,source=str(source.relative_to(ROOT)),sourceSha256=hashlib.sha256(original).hexdigest(),target=str(target.relative_to(ROOT)),targetSha256=hashlib.sha256(encoded).hexdigest(),sourceBytes=len(original),targetBytes=len(encoded),segments=len(model.Segments),entityRecords=sum(len(segment.Records) for segment in model.Segments),histories=[dict(name=body.PartName,model=type(body.History).__name__,header=asdict(body.History.Header)) for body in model.Bodies],snapshots=[dict(name=part.Name,model=type(part.Snapshot).__name__,header=asdict(part.Snapshot.Header)) for part in model.Snapshots],meshParts=len(model.Meshes),materialParts=len(model.Materials),graphicsObjects=len(model.Graphics.Objects) if model.Graphics else 0,memberNamesEqual=set(before)==set(after),changedMembers=[name for name in before if after.get(name)!=before[name]],parameterEdit=dict(name='d3',expression='8 mm',previous='6 mm') if label=='TriangularPipe' else None))
        (output/'Preparation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(label,len(encoded),report['cases'][-1]['targetSha256'],flush=True)
    report['status']='prepared'
    (output/'Preparation.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':
    main()
