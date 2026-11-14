import collections
import json
import sys
from pathlib import Path


def key(value):
    return json.dumps(value, sort_keys=True)


def main():
    decoded = json.loads(Path(sys.argv[1]).read_text())
    seen = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    units = collections.defaultdict(set)
    for control in decoded.values():
        if 'error' in control:
            continue
        unique = {asset['instance']: asset for asset in control['assets']}
        for asset in unique.values():
            for name, value in asset['properties'].items():
                if isinstance(value, dict) and 'links' in value:
                    value = {'links': len(value['links']['Targets']), 'enabled': value['links']['Enabled']}
                if isinstance(value, dict) and 'UnitCode' in value:
                    units[asset['schema'] + '.' + name].add(value['UnitCode'])
                seen[asset['schema']][name][key(value)] += 1
    schema = sys.argv[2] if len(sys.argv) > 2 else None
    for name, fields in sorted(seen.items()):
        if schema and name != schema:
            continue
        print('==', name)
        for field, values in sorted(fields.items()):
            top = values.most_common(3)
            print('  ', field, len(values), [(text[:60], count) for text, count in top])
    if schema is None:
        print(json.dumps({name: sorted(codes) for name, codes in sorted(units.items())}))


if __name__ == '__main__':
    main()
