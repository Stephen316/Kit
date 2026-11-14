import collections
import hashlib
import json
import lzma
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
API = runpy.run_path(str(DIRECTORY / 'DecodeGraph.py'))


def main():
    path = DIRECTORY.parents[1] / 'LocalOracle/Features/extrude_07mm.f3d'
    archive = API['TOOLS']['read_archive'](path)
    schema_raw = API['SCHEMA_PATH'].read_bytes()
    schema = {item['identifier'].upper(): item for item in json.loads(schema_raw)['metatypes']}
    classes = {}
    kinds = collections.Counter()
    for code, declaration in archive['classes'].items():
        entity = schema[declaration['identifier'].upper()]
        version = declaration['schemaVersion']
        lookup = next((item for item in entity.get('member_set_lookups') or [] if item['lookup_version'] == version), None)
        own = lookup['member_sets'][0] if lookup else {}
        members = [member for member in own.get('members') or [] if member['option_mask'] & 1]
        records = [record for record in archive['records'] if record['classCode'] == code]
        classes[declaration['identifier']] = {'name': entity['name'], 'version': version, 'reflectionCurrentVersion': entity['metatype_current_version'], 'base': declaration['baseIdentifier'], 'lookupStatus': lookup['lookup_status'] if lookup else 'absent', 'primaryRecords': sum(record['primary'] for record in records), 'continuationRecords': sum(not record['primary'] for record in records), 'members': [member | {'cppType': API['TOOLS']['demangle'](member['debug_type_name'])} for member in members]}
        kinds.update(member['metatype']['name'] for member in members)
    evidence = {'schema': 'FusionEntityGraphInventory/1', 'schemaSha256': hashlib.sha256(schema_raw).hexdigest(), 'archive': path.name, 'classCount': len(classes), 'recordCount': len(archive['records']), 'memberTypes': dict(kinds), 'classes': classes}
    raw = (json.dumps(evidence, indent=2) + '\n').encode()
    compressed = lzma.compress(raw, preset=9)
    (DIRECTORY / 'GraphInventory.json').write_bytes(raw)
    (DIRECTORY / 'GraphInventory.json.xz').write_bytes(compressed)
    summary = {key: value for key, value in evidence.items() if key != 'classes'}
    summary.update({'evidence': 'GraphInventory.json.xz', 'uncompressedSha256': hashlib.sha256(raw).hexdigest(), 'compressedSha256': hashlib.sha256(compressed).hexdigest(), 'uninitializedClasses': [{'identifier': key, 'name': value['name'], 'version': value['version']} for key, value in classes.items() if value['lookupStatus'] != 'initialized']})
    (DIRECTORY / 'GraphInventorySummary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
