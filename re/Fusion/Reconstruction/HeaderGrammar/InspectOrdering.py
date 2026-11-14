import hashlib
import json
from pathlib import Path
import runpy
from zipfile import ZipFile

root = Path(__file__).resolve().parents[4]
reader_type = runpy.run_path(str(root / 're/Fusion/Reconstruction/ReflectedFeatures.py'))['Reader']
inventory = json.loads((root / 're/Fusion/Reconstruction/CorpusInventory.json').read_text())
counts = {'archives': 0, 'segments': 0, 'primary_records': 0, 'continuation_records': 0, 'metadata_order_descents': 0, 'physical_id_descents': 0}
errors = []
exceptions = []
for source in inventory['files']:
    path = root / source['path']
    counts['archives'] += 1
    with ZipFile(path) as archive:
        for member in archive.namelist():
            if not member.endswith('/MetaStream.dat'):
                continue
            try:
                payload = archive.read(member)
                reader = reader_type(payload)
                kind = reader.text()
                segment_id = reader.number('I')
                reader.text(True)
                magic = reader.number('I')
                version = reader.number('I')
                if magic != 1234 or version != 8:
                    raise ValueError(f'Unsupported metadata magic/version {magic}/{version}')
                reader.take(8)
                reader.text()
                reader.text()
                reader.number('I')
                for _ in range(reader.count()):
                    reader.text(True)
                for _ in range(reader.count()):
                    reader.text()
                    reader.text()
                    reader.number('I')
                    reader.text()
                    reader.take(8 * reader.count())
                reader.take(8 * reader.count())
                primary = [(reader.number('Q'), reader.number('Q')) for _ in range(reader.count())]
                continuation = [(reader.number('Q'), reader.number('Q')) for _ in range(reader.count())]
                physical = sorted(primary + continuation, key=lambda row: row[1])
                metadata_descents = sum(a[0] > b[0] for table in (primary, continuation) for a,b in zip(table,table[1:]))
                physical_descents = sum(a[0] > b[0] for a,b in zip(physical,physical[1:]))
                counts['segments'] += 1
                counts['primary_records'] += len(primary)
                counts['continuation_records'] += len(continuation)
                counts['metadata_order_descents'] += metadata_descents
                counts['physical_id_descents'] += physical_descents
                if metadata_descents or physical_descents:
                    exceptions.append({'archive':source['path'],'member':member,'kind':kind,'segment_id':segment_id,'sha256':hashlib.sha256(payload).hexdigest(),'metadata_descents':metadata_descents,'physical_descents':physical_descents,'first_physical_descents':[(a,b) for a,b in zip(physical,physical[1:]) if a[0]>b[0]][:8]})
            except Exception as failure:
                errors.append({'archive':source['path'],'member':member,'error':str(failure)})
report = {'scope':'Read-only corpus metadata observation; no production codec execution or tests','counts':counts,'exceptions':exceptions,'errors':errors}
Path(__file__).with_name('OrderingCorpus.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'counts':counts,'exceptions':len(exceptions),'errors':len(errors)}))
