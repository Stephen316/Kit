"""Record-level round trip of complex records inside members that fail as a whole.

A member can fail for reasons unrelated to geometry (attribute families, record
quotas). This checks that every complex record inside it still reads and
re-emits token for token through the production typed nodes.
"""
import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(HERE))

import AsmScan  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import EntitySubtree  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import DefinedName, WalkSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import ReadEntityNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode  # noqa: E402
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord  # noqa: E402

COMPLEX = ('spline-surface', 'intcurve-curve', 'pcurve', 'tcoedge-coedge', 'tedge-edge', 'tvertex-vertex')


def freeze(value):
    return tuple(freeze(item) for item in value) if isinstance(value, list) else value


def main():
    verify = json.loads((HERE / 'VerifyComplex.json').read_text())
    failing = [item for item in verify['members'] if item.get('status') != 'exact']
    rows = []
    for item in failing:
        with zipfile.ZipFile(ROOT / item['path']) as archive:
            data = archive.read(item['member'])
        _, _, records = AsmScan.records(data)
        counts = collections.Counter()
        for record in records:
            if record['name'] not in COMPLEX:
                continue
            original = AsmRecord(record['name'], tuple((tag, freeze(value)) for tag, value in record['tokens']))
            try:
                node = ReadEntityNode(original)
                same = MakeEntityNode(node) == original
                kinds = sorted({DefinedName(found) for found in WalkSubtypes(EntitySubtree(node))})
                counts[(record['name'], ','.join(kinds), 'exact' if same else 'differs')] += 1
            except ValueError as error:
                counts[(record['name'], '', 'error: ' + str(error))] += 1
        rows.append(dict(path=item['path'], member=item['member'], memberError=item.get('error'), records=[dict(name=key[0], subtypes=key[1], status=key[2], count=count) for key, count in sorted(counts.items())]))
        print(item['path'], item['member'][-10:], item.get('error'))
        for key, count in sorted(counts.items()):
            print('   ', count, key)
    (HERE / 'VerifyRecords.json').write_text(json.dumps(rows, indent=1) + '\n')


if __name__ == '__main__':
    main()
