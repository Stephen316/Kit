import collections
import hashlib
import json
import lzma
from pathlib import Path
import runpy
from zipfile import ZipFile

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
read = runpy.run_path(str(root / 're/Fusion/Reconstruction/BrepTokens.py'))['read_stream']


def read_delta(record):
    fields = record['fields']
    position = 0
    def take(tag):
        nonlocal position
        field = fields[position]
        position += 1
        if field['tag'] != tag:
            raise ValueError(f'Expected tag {tag}, got {field["tag"]} at field{position-1}')
        return field['value']
    state = dict(zip(('stateId','backward','hidden','previousNode','nextNode','partnerNode','mergedWithNode','ownerStream'), [take(tag) for tag in (4,4,4,12,12,12,12,12)]))
    present = fields[position]['tag']; position += 1
    if present not in (10,11):
        raise ValueError('Invalid name presence flag')
    state['name'] = take(7) if present == 10 else None
    boards = []
    while take(4) != 0:
        board = {'ownerNode':take(12), 'status':take(4), 'changes':[]}
        while take(4) != 0:
            old,new=take(12),take(12)
            if old == new == -1:
                raise ValueError('Empty bulletin')
            board['changes'].append({'old':old,'new':new,'kind':'insert' if old == -1 else 'delete' if new == -1 else 'replace'})
        boards.append(board)
    state['boards'] = boards
    dependencies = take(4)
    state['stateList48'] = [take(12) for _ in range(dependencies)]
    if position != len(fields):
        raise ValueError('Trailing delta fields')
    return state


def inspect(data):
    parsed = read(data)
    records = parsed['records']
    pivot = next(index for index, value in enumerate(records) if value['name']=='history_stream')
    section = next(index for index, value in enumerate(records) if value['boundary_marker']=='End-of-ASM-History-Section')
    states = [read_delta(value) for value in records[pivot+1:section]]
    archived = [value for value in records[section:] if value['name']!='End-of-ASM-data']
    preamble = [field['value'] for field in records[pivot]['fields']]
    return {'activeCount':pivot,'preamble':preamble,'states':states,'archivedCount':len(archived),'archivedKinds':dict(collections.Counter(value['name'] for value in archived)), 'archiveStartPhysical':section}, parsed


def main():
    samples=json.loads((root/'re/Fusion/Reconstruction/TaperedHistory/CandidateHistories.json').read_text())['samples']
    paths={root/item['source']['path'] for item in samples}
    paths.update((root/'re/Fusion/LocalOracle').rglob('vendor*.f3d'))
    output=[]; allparsed={}; seen={}; failures=[]
    for path in sorted(paths):
        with ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith('.smbh'):continue
                payload=archive.read(name); digest=hashlib.sha256(payload).hexdigest()
                source={'path':str(path.relative_to(root)), 'member':name, 'sha256':digest, 'bytes':len(payload)}
                if digest in seen:
                    seen[digest]['sources'].append(source);continue
                try:
                    model,parsed=inspect(payload)
                    entry={'sources':[source], **model};output.append(entry);seen[digest]=entry
                    if len(model['states'])!=2 or model['preamble'][0]!=model['preamble'][1]:
                        allparsed[digest]=parsed
                except Exception as error:
                    failures.append({'source':source,'error':repr(error)})
    summary={'uniqueHistories':len(output),'sourceHistories':sum(len(entry['sources']) for entry in output),'failures':failures,'stateCounts':dict(collections.Counter(len(entry['states']) for entry in output)),'entries':output}
    encoded = lzma.compress(json.dumps(summary, separators=(',', ':')).encode())
    (out/'Inventory.json.xz').write_bytes(encoded)
    compact = {key: value for key, value in summary.items() if key != 'entries'}
    compact.update(evidence='Inventory.json.xz', evidenceSha256=hashlib.sha256(encoded).hexdigest(), entries=[{'sources': entry['sources'], 'activeCount': entry['activeCount'], 'preamble': entry['preamble'], 'stateIds': [state['stateId'] for state in entry['states']], 'archivedCount': entry['archivedCount']} for entry in output])
    (out/'Inventory.json').write_text(json.dumps(compact,indent=2)+'\n')
    (out/'ExtendedTokens.json.xz').write_bytes(lzma.compress(json.dumps(allparsed,separators=(',',':')).encode()))
    print(json.dumps({key:value for key,value in summary.items() if key!='entries'},indent=2))
    for entry in output:
        if len(entry['states'])!=2 or entry['preamble'][0]!=entry['preamble'][1]:
            print(entry['sources'][0]['path'],entry['preamble'],'states',[(state['stateId'],state['previousNode'],state['nextNode'],state['partnerNode'],state['mergedWithNode'],len(state['boards']),sum(len(board['changes']) for board in state['boards'])) for state in entry['states']],'archive',entry['archivedCount'])


if __name__=='__main__':main()
