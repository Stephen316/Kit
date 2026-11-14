import collections
import hashlib
import json
import lzma
from pathlib import Path
import runpy
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
READ=runpy.run_path(str(ROOT/'re/Fusion/Reconstruction/BrepTokens.py'))['read_stream']


def main():
    cases=json.loads(lzma.decompress((ROOT/'re/Fusion/Reconstruction/RoundCarriers/Controls.json.xz').read_bytes()))
    details=[]
    for case in cases:
        with ZipFile(ROOT/case['path']) as archive:
            payload=archive.read(case['member'])
        parsed=READ(payload)
        records=[]
        for record in parsed['records']:
            if record['boundary_marker'] or record['name']=='End-of-ASM-data':
                break
            records.append(record)
        faces=[]
        for index,record in enumerate(records):
            if record['name']!='face':
                continue
            surface=record['fields'][7]['value']
            if records[surface]['name'] not in ('sphere-surface','torus-surface'):
                continue
            faces.append(dict(index=index,surfaceRef=surface,surfaceKind=records[surface]['name'],firstLoop=record['fields'][4]['value'],nextFace=record['fields'][3]['value'],flags=record['fields'][8:]))
        details.append(dict(path=case['path'],member=case['member'],sha256=hashlib.sha256(payload).hexdigest(),records=records,roundFaces=faces))
    data=lzma.compress(json.dumps(details,separators=(',',':')).encode())
    (OUT/'Topology.json.xz').write_bytes(data)
    summary=dict(schema='FusionRoundTopology/1',details='Topology.json.xz',sha256=hashlib.sha256(data).hexdigest(),members=[dict(path=row['path'],member=row['member'],sha256=row['sha256'],entityCount=len(row['records']),kinds=dict(collections.Counter(rec['name'] for rec in row['records'])),roundFaces=row['roundFaces']) for row in details])
    (OUT/'TopologySummary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for row in summary['members']:
        print(row['path'],row['member'].rsplit('.',1)[-1],row['entityCount'],row['kinds'],[(face['surfaceKind'],face['firstLoop']) for face in row['roundFaces']])


if __name__=='__main__':
    main()
