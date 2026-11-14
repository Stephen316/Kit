"""Build header-tail variants that test whether Fusion needs the four short values after the header handles.

Every control DWG has 77 bits after the 47 header handle references. They read as four BS values, each
with the 00 code and a 16-bit value, then five bits of the 0x55 fill pattern. The ODA specification lists
four unknown BS values at the end of the header variables. Kit's authored shell wrote none of them, and
F7ZeroHeaderTail and Q11AuthoredShell, which also have none, both stalled on open.

* U1ZeroShorts is Q1NoDataStore with four zero BS values (code 10 each) after the handles;
* U2ForeignTail is Q1NoDataStore with the 77 tail bits of the A2 control, to learn whether the values are checked;
* U4AuthoredShellTail is Q11AuthoredShell with the 77 tail bits of its own A1 control.

U1ZeroShorts stalled for 453 s while Q1NoDataStore opens. Every DWG that Fusion exported carried four full
BS values that change on every save, then the 0x55 fill. Kit's shell now writes four values taken from the
version GUID and fills the rest of the byte with 0x55. Two more variants follow:

* U9OwnShortsZeroPad is Q1NoDataStore with its own four values and zero fill bits;
* U12AuthoredShellShorts is the H1NoAcm objects in Kit's current shell, with the shorts from the version GUID.
"""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildPruned6  # noqa: E402
import BuildPruned7  # noqa: E402
import BuildVariants  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import DayTime  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorShell import AuthorShell  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import MakeFrame  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

ZERO_SHORTS = MakeFrame(8, 0b10101010, b'')


def frame(dwg):
    return dict(dwg.SectionVars)['AcDb:Header']


def with_frame(dwg, value):
    rows = tuple((name, value if name == 'AcDb:Header' else record) for name, record in dwg.SectionVars)
    return replace(dwg, SectionVars=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--foreign', required=True, help='A2 control drawing whose header tail U2ForeignTail borrows')
    parser.add_argument('--source', required=True)
    parser.add_argument('--only', nargs='*', default=[])
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    foreign = ReadDwgFile(BuildVariants.database(Path(args.foreign).read_bytes()))
    flat, _ = BuildPruned6.cleared(BuildPruned6.h1_base(drawing))
    q1 = BuildPruned.without_sections(flat, (BuildPruned6.DATA_STORE,))
    shell = ReadDwgFile(AuthorShell(flat.DwgObjects, flat.HeaderVars, flat.ClassTable.ClassRows, DayTime(BuildPruned7.MOMENT)))
    width, bits = (item.FieldValue for item in frame(q1).RecordFields[:2])
    rows = (
        ('U1ZeroShorts', with_frame(q1, ZERO_SHORTS)),
        ('U2ForeignTail', with_frame(q1, frame(foreign))),
        ('U4AuthoredShellTail', with_frame(shell, frame(q1))),
        ('U9OwnShortsZeroPad', with_frame(q1, MakeFrame(width, bits >> 5 << 5, b''))),
        ('U12AuthoredShellShorts', shell),
    )
    if args.only:
        rows = tuple(row for row in rows if row[0] in args.only)
    plan = {'base_objects': len(flat.DwgObjects), 'variants': []}
    for label, dwg in rows:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        entry = BuildPruned2.record(out, label, bundle, data, dwg, {})
        tail = dict(ReadDwgFile(data).SectionVars)['AcDb:Header'].RecordFields
        entry['tail'] = {item.FieldName: item.FieldValue for item in tail if item.FieldName == 'TailWidth'}
        plan['variants'].append(entry)
    kept = json.loads((out / 'Plan10.json').read_text())['variants'] if (out / 'Plan10.json').exists() else []
    built = {row['label'] for row in plan['variants']}
    plan['variants'] = [row for row in kept if row['label'] not in built] + plan['variants']
    (out / 'Plan10.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
