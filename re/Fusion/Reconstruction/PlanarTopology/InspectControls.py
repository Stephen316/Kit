import hashlib
import json
import lzma
from pathlib import Path
import runpy
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
READ=runpy.run_path(str(ROOT/'re/Fusion/Reconstruction/JournalStates/InspectJournals.py'))['inspect']
BASE=runpy.run_path(str(ROOT/'re/Fusion/Reconstruction/JournalStates/Materialize.py'))


def decode(record):
    if record['name'] not in ('straight-curve','transform'):
        return BASE['entity'](record)
    values=BASE['Fields'](record)
    fields=dict(attribute=values.take(12),entityTag=values.take(4))
    if record['name']=='straight-curve':
        fields.update(reservedRef=values.take(12),originCm=values.take(19),direction=values.take(20),lowerBound=values.bound(),upperBound=values.bound())
    else:
        fields.update(columnX=values.take(20),columnY=values.take(20),columnZ=values.take(20),translationCm=values.take(20),scale=values.take(6),rotation=values.boolean(),reflection=values.boolean(),shear=values.boolean())
    values.done()
    return dict(kind=record['name'],fields=fields)


def main():
    sources=(('Tetrahedron','re/Fusion/Study/meshconverts-4b42d39fb1d5/faceted_closed.f3d'),('TriangularPipe','re/Fusion/Study/pipemodes-87cfa7d8d82b/triangular.f3d'))
    output=[]
    for label,path in sources:
        with ZipFile(ROOT/path) as archive:
            for member in archive.namelist():
                if not member.endswith('.smbh'):continue
                payload=archive.read(member);frame,stream=READ(payload)
                entities=[decode(record) for record in stream['records'][:frame['activeCount']]]
                output.append(dict(label=label,path=path,member=member,sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),frame=frame,header=stream['header'],entities=entities))
    data=lzma.compress(json.dumps(output,separators=(',',':')).encode());(OUT/'Controls.json.xz').write_bytes(data)
    summary=dict(schema='FusionPlanarHistoryControls/1',scope='Read-only complete named-field research decoding of initial geometry and full journal framing; no production execution',details='Controls.json.xz',sha256=hashlib.sha256(data).hexdigest(),sources=[{key:row[key] for key in ('label','path','member','sha256','bytes','frame')} for row in output])
    (OUT/'ControlSummary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for row in output:
        print(row['label'],row['path'],row['member'],row['sha256'],row['frame']['activeCount'],row['frame']['preamble'])
        for index,entity in enumerate(row['entities']):
            if entity['kind'] in ('body','point','plane-surface'):
                print(index,entity)

if __name__=='__main__':main()
