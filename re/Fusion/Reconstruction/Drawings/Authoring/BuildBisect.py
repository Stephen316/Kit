"""Build content-bisection variants for the two causes that stall the open of a Kit-authored DWG.

Every B variant starts from Q1NoDataStore, the A1 control without AutoCAD Mechanical objects, unused blocks
and the data-store section. Q1NoDataStore opens in about 5 s and keeps the four header values that Fusion
wrote into the A1 control.

Cause 1 changes one input at a time and keeps those four values. A stall means that the values depend on
that input. The B labels are:

* B0Base is Q1NoDataStore emitted again, as the open control of the round;
* B1VersionGuid, B2Fingerprint, B3TdUpdate, B4TdCreate, B5TdInDwg, B6HandSeed and B7Extents change
  the header variables that differ between the Fusion saves;
* B8UserReal changes USERR4, a header variable that is the same in every save;
* B9AllVaried changes every header variable of B1 to B7 together;
* B10FifthLong writes 1 as the BL value that follows the four BS values.

Cause 2 starts from Q8AuthoredSections, which has Kit's section set and opens. YAX, which adds Kit's AppInfo and
Kit's auxiliary header, stalled twice. The C labels split those two parts:

* C1AppNoTrust keeps the Fusion product entry and drops the trusted-file entry;
* C2AppKitProduct has Kit's product entry and keeps the trusted-file entry;
* C3AuxCounts, C4AuxReserved, C5AuxTimes and C6AuxSeed each take one group of Kit's auxiliary header values,
  together with Kit's whole AppInfo;
* C7AppOnly and C8AuxOnly repeat Kit's AppInfo and Kit's auxiliary header alone on Q8AuthoredSections;
* C9AppAux and C10Summary rebuild the YAX and YS pair variants. Their DWGs equal those of YAX and YS byte
  for byte, as C8AuxOnly equals YX and Q8AuthoredSections equals Y0.

Results in Fusion 2706.1.17, with a 60 s stall limit (BisectRound.py, SummarizeBisect.py):

* B0Base opened in 4.4 s and B10FifthLong in 3.5 s;
* B8UserReal, B9AllVaried and B1VersionGuid stalled, so the four values cover the header data and strings;
* B2 to B7 were not run, because one shared header variable already stalls the open;
* C7AppOnly and C1AppNoTrust stalled, and C2AppKitProduct opened in 3.5 s. The open needs the Autodesk
  trusted-file text in AppInfo or AppInfoHistory. Q8AuthoredSections drops AppInfoHistory, so Kit's AppInfo
  removes the last copy of that text. The auxiliary header is not involved, so C3 to C6 and C8 were not run.

Kit does not write the trusted-file text, because it states an Autodesk save.
"""

import argparse
import json
import sys
import uuid
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
from convert.formats.Fusion.DrawingCodec.Dwg.Author.ShellParts import AuthorAppInfo, AuthorSummary, AuxHeader  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import MakeFrame  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgField, DwgRecord  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import AsHandle  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import NamedValue  # noqa: E402

PLAN = 'PlanBisect.json'
AUX_GROUPS = {
    'counts': ('SaveCount', 'SavesPartOne', 'SavesPartTwo', 'SavesDelta', 'SaveCountAgain'),
    'reserved': ('ReservedG', 'ReservedK'),
    'times': ('TdCreateDay', 'TdCreateMsec', 'TdUpdateDay', 'TdUpdateMsec'),
    'seed': ('HandSeed',),
}


def guid(label):
    return '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'kit-bisect:' + label)).upper() + '}'


def with_vars(dwg, values):
    names = {item.FieldName for item in dwg.HeaderVars.RecordFields}
    missing = set(values) - names
    if missing:
        raise ValueError(f'header lacks {sorted(missing)}')
    fields = tuple(DwgField(item.FieldName, values.get(item.FieldName, item.FieldValue)) for item in dwg.HeaderVars.RecordFields)
    return replace(dwg, HeaderVars=DwgRecord(fields))


def var(dwg, name):
    return NamedValue(dwg.HeaderVars, name)


def section(dwg, name):
    return dict(dwg.SectionVars)[name]


def with_section(dwg, name, record):
    return replace(dwg, SectionVars=tuple((key, record if key == name else value) for key, value in dwg.SectionVars))


def with_fields(record, values):
    return DwgRecord(tuple(DwgField(item.FieldName, values.get(item.FieldName, item.FieldValue)) for item in record.RecordFields))


def fifth_long(dwg, value):
    width, bits = (item.FieldValue for item in section(dwg, 'AcDb:Header').RecordFields[:2])
    if width != 77 or bits & 0b11111 != 0b10101:
        raise ValueError('unexpected header tail')
    shorts = bits >> 5
    long_bits = int.from_bytes(value.to_bytes(4, 'little'), 'big')
    return with_section(dwg, 'AcDb:Header', MakeFrame(72 + 34, (shorts << 34) | long_bits, b''))


def header_rows(q1):
    later = var(q1, 'TdUpdateMsec') + 60000
    seed = AsHandle(var(q1, 'HandSeed'))
    low, high = var(q1, 'PExtMin'), var(q1, 'PExtMax')
    singles = {
        'B1VersionGuid': {'VersionGuid': guid('B1VersionGuid')},
        'B2Fingerprint': {'FingerprintGuid': guid('B2Fingerprint')},
        'B3TdUpdate': {'TdUpdateMsec': later},
        'B4TdCreate': {'TdCreateMsec': var(q1, 'TdCreateMsec') - 60000},
        'B5TdInDwg': {'TdInDwgMsec': var(q1, 'TdInDwgMsec') + 1000, 'TdUsrTimerMsec': var(q1, 'TdUsrTimerMsec') + 1000},
        'B6HandSeed': {'HandSeed': DwgHandleRef(seed.RefCode, seed.RefValue + 16)},
        'B7Extents': {'PExtMin': (0.0, 0.0, 0.0), 'PExtMax': (420.0, 297.0, 0.0) if high != (420.0, 297.0, 0.0) else (421.0, 297.0, 0.0)},
    }
    if low == (0.0, 0.0, 0.0):
        singles['B7Extents'] = {'PExtMax': (421.0, 297.0, 0.0)}
    rows = [('B0Base', q1)]
    rows += [(label, with_vars(q1, values)) for label, values in singles.items()]
    rows.append(('B8UserReal', with_vars(q1, {'UserRFour': 1.0})))
    merged = {}
    for values in singles.values():
        merged.update(values)
    rows.append(('B9AllVaried', with_vars(q1, merged)))
    rows.append(('B10FifthLong', fifth_long(q1, 1)))
    return rows


def shell_rows(q8, moment):
    seed = AsHandle(var(q8, 'HandSeed')).RefValue
    kit_aux = AuxHeader(seed, moment)
    kit_values = {item.FieldName: item.FieldValue for item in kit_aux.RecordFields}
    fusion_aux = section(q8, 'AcDb:AuxHeader')
    fusion_app = q8.AppInfo
    kit_app = AuthorAppInfo()
    no_trust = DwgAppInfo(fusion_app.LeadWord, fusion_app.InfoName, fusion_app.AppEntries[:1])
    kit_product = DwgAppInfo(fusion_app.LeadWord, fusion_app.InfoName, kit_app.AppEntries + fusion_app.AppEntries[1:])
    rows = [
        ('C1AppNoTrust', with_section(replace(q8, AppInfo=no_trust), 'AcDb:AuxHeader', kit_aux)),
        ('C2AppKitProduct', with_section(replace(q8, AppInfo=kit_product), 'AcDb:AuxHeader', kit_aux)),
    ]
    for index, (group, names) in enumerate(AUX_GROUPS.items(), start=3):
        record = with_fields(fusion_aux, {name: kit_values[name] for name in names})
        rows.append((f'C{index}Aux{group.title()}', with_section(replace(q8, AppInfo=kit_app), 'AcDb:AuxHeader', record)))
    rows.append(('C7AppOnly', replace(q8, AppInfo=kit_app)))
    rows.append(('C8AuxOnly', with_section(q8, 'AcDb:AuxHeader', kit_aux)))
    rows.append(('C9AppAux', with_section(replace(q8, AppInfo=kit_app), 'AcDb:AuxHeader', kit_aux)))
    rows.append(('C10Summary', replace(q8, Summary=AuthorSummary(moment))))
    return rows


def bases(drawing):
    flat, _ = BuildPruned6.cleared(BuildPruned6.h1_base(drawing))
    q1 = BuildPruned.without_sections(flat, (BuildPruned6.DATA_STORE,))
    q8 = BuildPruned6.renumbered(BuildPruned.without_sections(flat, BuildPruned7.DROPPED))
    return q1, q8


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--only', nargs='*', default=[])
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    q1, q8 = bases(drawing)
    rows = header_rows(q1) + shell_rows(q8, DayTime(BuildPruned7.MOMENT))
    if args.only:
        rows = [row for row in rows if row[0] in args.only]
    plan = {'variants': []}
    for label, dwg in rows:
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        entry = BuildPruned2.record(out, label, bundle, data, dwg, {})
        entry['tail_width'] = section(ReadDwgFile(data), 'AcDb:Header').RecordFields[0].FieldValue
        plan['variants'].append(entry)
    path = out / PLAN
    kept = json.loads(path.read_text())['variants'] if path.exists() else []
    built = {row['label'] for row in plan['variants']}
    plan['variants'] = [row for row in kept if row['label'] not in built] + plan['variants']
    path.write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps([(row['label'], row['dwg_sha256'][:8], row['dwg_bytes'], row.get('tail_width')) for row in plan['variants']]))


if __name__ == '__main__':
    main()
