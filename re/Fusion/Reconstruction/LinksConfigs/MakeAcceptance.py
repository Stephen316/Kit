import hashlib
import json
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
oracle = repository / 're/Fusion/LocalOracle/LinksConfigs'
private = oracle / 'tmp'


def load(name):
    path = private / name
    return json.loads(path.read_text()) if path.exists() else None


def clean(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in ('traceback', 'close_errors'):
                lines = [line for line in str(item).splitlines() if line.strip()]
                result[key + '_last_line'] = lines[-1] if lines else None
            else:
                result[key] = clean(item)
        return result
    if isinstance(value, list):
        return [clean(item) for item in value]
    return value


prepared = load('accept/Prepare.json')
report = {
    'scope': 'Native Fusion acceptance of Kit ReadDocument and EmitParsed outputs for designs with external references',
    'prepared_outputs': prepared['outputs'],
    'files': [],
    'runs': {},
}
for entry in prepared['outputs']:
    data = (private / 'accept' / (entry['name'] + '.f3d')).read_bytes()
    report['files'].append({'name': entry['name'] + '.f3d', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
for run, name in (('Accept1', 'AcceptLinkReplay.json'), ('Accept2_upload', 'BeginLinkUpload.json'), ('Accept2', 'AcceptLinkUploads.json'), ('SaveProbe', 'ProbeLinkSave.json'), ('Accept2_saves', 'AcceptLinkSaves.json'), ('FolderState', 'InspectLinkUpload.json')):
    value = load(name)
    if value is not None:
        report['runs'][run] = clean(value)
text = json.dumps(report, indent=2) + '\n'
if str(Path.home()) in text:
    raise SystemExit('private path in acceptance report')
(oracle / 'LinkAcceptance.json').write_text(text)
print('runs', sorted(report['runs']), 'sha256', hashlib.sha256(text.encode()).hexdigest())
