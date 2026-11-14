"""Build shell variants that separate Kit's authored DWG shell from its authored objects.

S5SheetDimension and T5SheetDimension, which differ only in their AppInfo, both left Documents.open
waiting in DrawingDocument::waitForOpenToComplete while the drawing engine sat idle.
N2AuthoredF2d, a Kit F2D around the H1NoAcm DWG, opened with every view and the dimension.
The wait therefore comes from the authored DWG. These variants keep the H1NoAcm objects and change
only the file shell, with every HasDsData bit cleared as in Q1NoDataStore:

* Q11AuthoredShell writes the H1NoAcm objects, header variables and classes through AuthorShell,
  so it has Kit's file header, sections, AppInfo, summary, auxiliary header and header tail;
* Q8AuthoredSections keeps the control shell but has only the authored section set, renumbered;
* Q10ZeroTail is Q1NoDataStore with the authored header tail, which has no bits after the handles.
"""

import argparse
import datetime
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildPruned6  # noqa: E402
import BuildVariants  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorDwg import DayTime  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorShell import AuthorShell  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import MakeFrame  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

MOMENT = datetime.datetime(2026, 11, 12, 12, 0, 0)
DROPPED = (BuildPruned6.DATA_STORE, 'AcDb:Preview', 'AcDb:AppInfoHistory')


def zero_tail(dwg):
    rows = tuple((name, MakeFrame(0, 0, b'') if name == 'AcDb:Header' else record) for name, record in dwg.SectionVars)
    return replace(dwg, SectionVars=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    flat, _ = BuildPruned6.cleared(BuildPruned6.h1_base(drawing))
    shell = AuthorShell(flat.DwgObjects, flat.HeaderVars, flat.ClassTable.ClassRows, DayTime(MOMENT))
    rows = (
        ('Q11AuthoredShell', ReadDwgFile(shell)),
        ('Q8AuthoredSections', BuildPruned6.renumbered(BuildPruned.without_sections(flat, DROPPED))),
        ('Q10ZeroTail', zero_tail(BuildPruned.without_sections(flat, (BuildPruned6.DATA_STORE,)))),
    )
    plan = {'base_objects': len(flat.DwgObjects), 'variants': []}
    for label, dwg in rows:
        data = shell if label == 'Q11AuthoredShell' else BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        entry = BuildPruned2.record(out, label, bundle, data, dwg, {})
        entry['sections'] = [(info.SectionName, info.SectionId) for info in dwg.SectionInfos if info.SectionName]
        plan['variants'].append(entry)
    (out / 'Plan9.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
