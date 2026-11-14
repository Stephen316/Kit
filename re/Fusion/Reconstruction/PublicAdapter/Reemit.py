from pathlib import Path
import hashlib
import json
import sys

root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root/'src'))
from convert import open_document, write_document
from interchange import CadDocument

out=root/'re/Fusion/LocalOracle/PublicAdapter'
rows=json.loads((out/'Preparation.json').read_text())
for row in rows:
    source=Path(row['source'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=row['sha256']:
        raise ValueError('Frozen source digest changed')
    document=open_document(source,source_format='f3d')
    neutral=out/(row['kind']+'.native.json')
    neutral.write_text(document.to_json())
    target=Path(row['reemit'])
    write_document(CadDocument.from_json(neutral.read_text()),target,destination_format='f3d',overwrite=True,allow_carrier=False)
    row['reemitSha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    row['nativeBytesEqual']=target.read_bytes()==source.read_bytes()
    row['nativeJsonSha256']=hashlib.sha256(neutral.read_bytes()).hexdigest()
    print(row['kind'], row['reemitSha256'], row['nativeBytesEqual'],flush=True)
(out/'Preparation.json').write_text(json.dumps(rows,indent=2)+'\n')
