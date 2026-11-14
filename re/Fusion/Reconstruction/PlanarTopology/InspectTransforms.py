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
DECODE=runpy.run_path(str(OUT/'InspectControls.py'))['decode']
DATA=json.loads(lzma.decompress((ROOT/'re/Fusion/Reconstruction/BrepCoverage/Inventory.json.xz').read_bytes()))


def main():
    seen=set();records=[];signatures=collections.Counter()
    for member in DATA['members']:
        digest=member['sha256']
        if digest in seen or 'transform' not in DATA['uniqueBlobs'][digest]['recordTypes']:continue
        seen.add(digest)
        with ZipFile(ROOT/member['path']) as archive: parsed=READ(archive.read(member['member']))
        for index,record in enumerate(parsed['records']):
            if record['name']!='transform':continue
            semantic=DECODE(record)['fields'];signature=tuple(field['tag'] for field in record['fields']);signatures[str(signature)]+=1
            records.append(dict(source=member,recordOrdinal=index,fields=semantic))
    packed=lzma.compress(json.dumps(records,separators=(',',':')).encode());(OUT/'Transforms.json.xz').write_bytes(packed)
    report=dict(schema='FusionTransformSemantics/1',scope='Read-only complete transform field decoding; no CAD runtime or production execution. The earlier static library inspection was removed.',records=len(records),distinctSourceBlobs=len(seen),fieldTagSignatures=dict(signatures),detailsSha256=hashlib.sha256(packed).hexdigest(),flagCombinations=dict(collections.Counter(str((row['fields']['rotation'],row['fields']['reflection'],row['fields']['shear'])) for row in records)),scales=dict(collections.Counter(str(row['fields']['scale']) for row in records)),fields=['attributeRef','entityTag','columnX','columnY','columnZ','translationCm','scale','rotation','reflection','shear'],mapping='world = scale * (x*columnX + y*columnY + z*columnZ) + translationCm',evidence='LocalOracle/PlanarTopology/NativeAcceptance.json accepted a placed tetrahedron with a nonidentity transform. Its persisted and reopened volume, centroid and bounds match this mapping, so the column convention and the unscaled translation hold. The flag names rotation, reflection and shear came from removed static evidence and are not confirmed by a black-box experiment; preserve the three flags independently.',nonidentityExamples=[row for row in records if row['fields']['translationCm'] != [0.0,0.0,0.0] or row['fields']['rotation'] or row['fields']['reflection'] or row['fields']['shear']][:5])
    (OUT/'TransformEvidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('records','distinctSourceBlobs','fieldTagSignatures','flagCombinations','scales')},indent=2))

if __name__=='__main__':main()
