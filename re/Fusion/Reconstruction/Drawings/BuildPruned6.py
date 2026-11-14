"""Build the data-store variants of H1NoAcm.

Both LAYOUT objects of every control set the HasDsData common bit, and every control carries an
AcDb:AcDsPrototype_1b section. D6Minimal dropped that section with the optional sections and kept the
bit, and Fusion answered "Drawing file is not valid.". These variants separate the two changes:

* Q1NoDataStore drops AcDb:AcDsPrototype_1b and clears the bit on every object;
* Q3NoOptional drops all four optional sections and clears the bit, which is the authored shell;
* Q2KeptDataFlag drops AcDb:AcDsPrototype_1b and keeps the bit.

Q1NoDataStore opened with every view and the dimension, and Q3NoOptional showed the same dialog as
D6Minimal. Q4 to Q6 therefore start from Q1NoDataStore and each drop one more optional section:

* Q4NoPreview drops AcDb:Preview;
* Q5NoRevHistory drops AcDb:RevHistory;
* Q6NoAppHistory drops AcDb:AppInfoHistory.

Removing sections leaves gaps in the section numbers, and Kit's authored shell had the same gaps.
Q7Renumbered is Q3NoOptional with its section numbers made contiguous again.
"""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildPruned4  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import Graph, prune  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

DATA_STORE = 'AcDb:AcDsPrototype_1b'


def h1_base(drawing):
    base = ReadDwgFile(BuildVariants.database(drawing))
    base, _, _ = prune(base, BuildPruned.unused_blocks(Graph(base)))
    graph = Graph(base)
    kill = BuildPruned.acm_objects(graph)
    pruned, _, _ = prune(base, kill | BuildPruned4.recompose_records(graph, graph.closure(kill)))
    return pruned


def cleared(dwg):
    """Clear HasDsData on every object and count the objects that had it set."""
    rows = []
    flagged = {}
    for item in dwg.DwgObjects:
        fields = item.CommonData.RecordFields
        if any(field.FieldName == 'HasDsData' and field.FieldValue for field in fields):
            flagged[item.ClassKind] = flagged.get(item.ClassKind, 0) + 1
            fields = tuple(DwgField('HasDsData', 0) if field.FieldName == 'HasDsData' else field for field in fields)
            item = replace(item, CommonData=DwgRecord(fields))
        rows.append(item)
    return replace(dwg, DwgObjects=tuple(rows)), flagged


def renumbered(dwg):
    """Number the named sections 1, 2, 3 and so on from the last, keeping their order."""
    named = [info for info in dwg.SectionInfos if info.SectionName]
    numbers = {info.SectionName: len(named) - index for index, info in enumerate(named)}
    infos = tuple(replace(info, SectionId=numbers[info.SectionName]) if info.SectionName else info for info in dwg.SectionInfos)
    return replace(dwg, SectionInfos=infos)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    base = h1_base(drawing)
    flat, flagged = cleared(base)
    rows = (
        ('Q1NoDataStore', BuildPruned.without_sections(flat, (DATA_STORE,))),
        ('Q3NoOptional', BuildPruned.without_sections(flat, BuildPruned.OPTIONAL_SECTIONS)),
        ('Q2KeptDataFlag', BuildPruned.without_sections(base, (DATA_STORE,))),
        ('Q4NoPreview', BuildPruned.without_sections(flat, (DATA_STORE, 'AcDb:Preview'))),
        ('Q5NoRevHistory', BuildPruned.without_sections(flat, (DATA_STORE, 'AcDb:RevHistory'))),
        ('Q6NoAppHistory', BuildPruned.without_sections(flat, (DATA_STORE, 'AcDb:AppInfoHistory'))),
        ('Q7Renumbered', renumbered(BuildPruned.without_sections(flat, BuildPruned.OPTIONAL_SECTIONS))),
    )
    plan = {'base_objects': len(base.DwgObjects), 'cleared_flags': flagged, 'variants': []}
    for label, dwg in rows:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        entry = BuildPruned2.record(out, label, bundle, data, dwg, {})
        entry['sections'] = [(info.SectionName, info.SectionId) for info in dwg.SectionInfos if info.SectionName]
        plan['variants'].append(entry)
    (out / 'Plan7.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
