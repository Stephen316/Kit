"""Build one-part shell hybrids that find which part of Kit's authored DWG shell stalls the drawing open.

Q1NoDataStore opens in about 5 s. U12AuthoredShellShorts, the same H1NoAcm objects in Kit's shell with
four header shorts from the version GUID, did not open within 460 s. Q8AuthoredSections showed that Kit's
section set is accepted. Each variant below is Q1NoDataStore with exactly one other part taken from Kit's shell:

* W1KitAppInfo has Kit's single ProductInformation entry instead of the Fusion product and trusted-file entries;
* W2KitShorts has the four header shorts that Kit derives from the version GUID;
* W3KitAuxHeader has Kit's auxiliary header, with a save count of 1;
* W4KitSummary has Kit's summary, with empty texts and the authoring moment;
* W5KitFreeSpace has Kit's object free-space record;
* W6KitClassCounts has class instance counts recounted from the objects.

The file header, encrypted header and page map follow from these parts when the file is written.
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
from convert.formats.Fusion.DrawingCodec.Dwg.Author.AuthorShell import CountClasses  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShellParts import AuthorAppInfo, AuthorSummary, AuxHeader, FreeSpace, SaveShorts  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import AsHandle, AsText  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import NamedValue  # noqa: E402


def with_section(dwg, name, record):
    rows = tuple((key, record if key == name else value) for key, value in dwg.SectionVars)
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
    q1 = BuildPruned.without_sections(flat, (BuildPruned6.DATA_STORE,))
    moment = DayTime(BuildPruned7.MOMENT)
    seed = AsHandle(NamedValue(q1.HeaderVars, 'HandSeed')).RefValue
    rows = (
        ('W1KitAppInfo', replace(q1, AppInfo=AuthorAppInfo())),
        ('W2KitShorts', with_section(q1, 'AcDb:Header', SaveShorts(AsText(NamedValue(q1.HeaderVars, 'VersionGuid'))))),
        ('W3KitAuxHeader', with_section(q1, 'AcDb:AuxHeader', AuxHeader(seed, moment))),
        ('W4KitSummary', replace(q1, Summary=AuthorSummary(moment))),
        ('W5KitFreeSpace', with_section(q1, 'AcDb:ObjFreeSpace', FreeSpace(len(q1.DwgObjects), moment))),
        ('W6KitClassCounts', replace(q1, ClassTable=replace(q1.ClassTable, ClassRows=CountClasses(q1.ClassTable.ClassRows, q1.DwgObjects).ClassRows))),
    )
    plan = {'base_objects': len(q1.DwgObjects), 'variants': []}
    for label, dwg in rows:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, {}))
    (out / 'Plan11.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps([(row['label'], row['sha256'][:8], row['dwg_bytes']) for row in plan['variants']]))


if __name__ == '__main__':
    main()
