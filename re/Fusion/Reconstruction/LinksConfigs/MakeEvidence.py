import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

oracle = repository / 're/Fusion/LocalOracle/LinksConfigs'
fixtures = oracle / 'Fixtures'
controls = json.loads((oracle / 'tmp/LinkControls.json').read_text())
configs = json.loads((oracle / 'tmp/ConfigControls.json').read_text())
reencoded = ('.protein', '.smb', '.smbh')


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def roundtrip(data):
    model = ReadDocument(data)
    output = EmitParsed(model)
    before, after = members(data), members(output)
    changed = sorted(name.rsplit('/', 1)[-1].split('.')[-1] for name in before if before[name] != after.get(name))
    return {
        'model_equal_after_reread': ReadDocument(output) == model,
        'member_count': len(before),
        'same_member_names': set(before) == set(after),
        'byte_identical_members': sum(before[name] == after.get(name) for name in before),
        'changed_member_kinds': changed,
        'changed_outside_reencoded_kinds': [name for name in before if before[name] != after.get(name) and not name.endswith(reencoded)],
        'root_links': len(model.Document.Links),
        'asset_links': len(model.Asset.Links),
        'contexts_per_segment': {segment.Metadata.Header.Segment.name: len(segment.Metadata.Contexts) for segment in model.Segments},
    }


report = {
    'fusion_version': controls['fusion_version'],
    'scope': 'Native external-reference controls exported from Fusion, sanitized, and replayed through ReadDocument and EmitParsed',
    'sanitization': 'Lineage keys become KitLinkLineageNNNNNNNN, the home directory becomes a generic user directory, the cache key becomes SYNTHCACHE000000, and root link paths become /synthetic/... with equal length',
    'controls': [],
    'configuration': {
        'status': 'blocked',
        'call': 'Design.createConfiguredDesign',
        'error': next((line for line in configs.get('traceback', '').splitlines()[::-1] if line.startswith('RuntimeError')), None),
        'plain_part_exported': [{'file': entry['file'], 'bytes': entry['bytes'], 'sha256': entry['sha256']} for step in configs.get('steps', []) for entry in step.get('exports', [])],
    },
}
archive = {'name': 'R9_archive', 'note': 'Saved root assembly exported through the F3Z archive option', 'exports': configs.get('link_archive', [])}
report['runs'] = {
    'link_controls': {'status': controls['status'], 'documents_after': controls['documents_after']},
    'configuration_controls': {'status': configs['status'], 'stage': configs['stage'], 'documents_after': configs['documents_after']},
}
for step in [*controls['steps'], archive]:
    for export in step.get('exports', []):
        stem = export['file'].replace('.f3z.f3d', '.f3d').removesuffix('.f3d')
        fixture = fixtures / f'{stem}.f3d'
        entry = {
            'name': step['name'],
            'note': step.get('note'),
            'native_export': {'file': export['file'], 'bytes': export['bytes'], 'sha256': export['sha256']},
            'native_occurrences': step.get('occurrences', []),
            'native_references': step.get('references', []),
            'native_joints': step.get('joints', []),
            'is_saved': step.get('is_saved'),
        }
        if fixture.exists():
            data = fixture.read_bytes()
            entry['fixture'] = {'path': str(fixture.relative_to(repository)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            entry['kit_replay'] = roundtrip(data)
        report['controls'].append(entry)
text = json.dumps(report, indent=2) + '\n'
if str(Path.home()) in text:
    raise SystemExit('private marker in evidence')
(oracle / 'LinkEvidence.json').write_text(text)
print('controls', len(report['controls']), 'fixtures', sum('fixture' in entry for entry in report['controls']))
