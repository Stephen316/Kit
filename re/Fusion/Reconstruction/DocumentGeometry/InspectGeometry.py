import collections
import hashlib
import json
import lzma
from pathlib import Path
import runpy
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
READ = runpy.run_path(str(ROOT / 're/Fusion/Reconstruction/BrepTokens.py'))['read_stream']
HISTORY = runpy.run_path(str(ROOT / 're/Fusion/Reconstruction/JournalStates/InspectJournals.py'))['inspect']
SOURCES = (
    'Study/meshconvertoperations-5af73924aa60/base_feature_closed.f3d',
    'Study/meshconvertoperations-5af73924aa60/base_feature_open.f3d',
    'Study/meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
    'Study/meshconverts-4b42d39fb1d5/faceted_closed.f3d',
    'Study/meshconverts-4b42d39fb1d5/faceted_open.f3d',
    'Study/pipemodes-87cfa7d8d82b/triangular.f3d',
    'LocalOracle/PublicAdapter/vendor_circleEdited.f3d',
    'LocalOracle/PublicAdapter/vendor_frustumEdited.f3d',
    'LocalOracle/PublicAdapter/vendor_extrusionEdited.f3d',
)


def main():
    entries = []
    details = []
    for name in SOURCES:
        path = ROOT / 're/Fusion' / name
        with ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.endswith(('.smb', '.smbh')):
                    continue
                data = archive.read(member)
                parsed = READ(data)
                frame = HISTORY(data)[0] if member.endswith('.smbh') else None
                records = parsed['records'][:frame['activeCount']] if frame else [value for value in parsed['records'] if value['name'] != 'End-of-ASM-data']
                entry = dict(source=str(path.relative_to(ROOT)), member=member, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), header=parsed['header'], records=len(records), kinds=dict(collections.Counter(value['name'] for value in records)), frame=frame)
                entry['nullPartners'] = [index for index, value in enumerate(records) if value['name'] == 'coedge' and value['fields'][5]['value'] == -1]
                entry['faceFlags'] = [value['fields'][8:] for value in records if value['name'] == 'face']
                entries.append(entry)
                details.append(dict(source=entry['source'], member=member, parsed=parsed))
                print(name, member.rsplit('/',1)[1], parsed['header'], 'rows',len(records),'kinds',entry['kinds'],'nullpartner',entry['nullPartners'])
                if frame:
                    print('journal',frame['preamble'],'states',len(frame['states']),'archived',frame['archivedCount'])
    (OUT/'Inventory.json').write_text(json.dumps(entries,indent=2)+'\n')
    encoded=lzma.compress(json.dumps(details,separators=(',',':')).encode())
    (OUT/'Tokens.json.xz').write_bytes(encoded)
    (OUT/'TokenIndex.json').write_text(json.dumps(dict(file='Tokens.json.xz',sha256=hashlib.sha256(encoded).hexdigest(),members=len(details)),indent=2)+'\n')


if __name__ == '__main__':
    main()
