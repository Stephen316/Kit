"""Verify typed subtype bodies against the complex corpus and the authored fixtures.

Run with python3.14 -I VerifyTyped.py [--src <src root>] [--out <json>] [--base-report <json> --base-label <commit>]
--src points at a production `src` tree, so the same walk signatures can be computed
for an older checkout (`git archive <commit> src`) and compared through --base-report.
Without --out the report goes to TypedVerify.json. Typed checks only run when the
Typed package exists in the selected tree.
"""
import argparse
import collections
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
ARGS = argparse.ArgumentParser()
ARGS.add_argument('--src', default=str(ROOT / 'src'))
ARGS.add_argument('--out', default=str(HERE / 'TypedVerify.json'))
ARGS.add_argument('--skip-authored', action='store_true')
ARGS.add_argument('--base-report')
ARGS.add_argument('--base-label')
OPTIONS = ARGS.parse_args()
sys.path.insert(0, OPTIONS.src)
sys.path.insert(1, str(BASE))

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import SubtypeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import EntitySubtree  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.RelinkSubtypes import RelinkSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import DefinedName, MapSubtypes, WalkSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef  # noqa: E402

try:
    from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedCodecs import KTypedCodecs, TreeBody, TypeBody  # noqa: E402
    from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.TypedRecord import KRecordTypes  # noqa: E402
except ImportError:
    KTypedCodecs = None


def signature(entries):
    return [f'ref:{value.Family}:{value.Index}' if isinstance(value, SubtypeRef) else DefinedName(value) for value in entries]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def typed_checks(entities, counts, problems):
    for entity in entities:
        for value in WalkSubtypes(EntitySubtree(entity)):
            if not isinstance(value, SubtypeNode) or value.SubtypeName not in KTypedCodecs:
                continue
            counts[value.SubtypeName] += 1
            if not isinstance(value.Body, KRecordTypes):
                problems.append(value.SubtypeName + ' body is not typed')
            elif TypeBody(value.SubtypeName, TreeBody(value.SubtypeName, value.Body)) != value.Body:
                problems.append(value.SubtypeName + ' typed body does not round trip')


def corpus(report):
    members = json.loads((BASE / 'VerifyComplex.json').read_text())['members']
    counts = collections.Counter()
    rows = []
    for member in members:
        if member['status'] != 'exact':
            continue
        with zipfile.ZipFile(ROOT / member['path']) as archive:
            payload = archive.read(member['member'])
        history = member['member'].endswith('.smbh')
        model = ReadJournal(payload) if history else ReadGeometry(payload)
        emitted = EmitJournal(model) if history else EmitGeometry(model)
        walks = [signature(WalkSubtypes(EntitySubtree(entity))) for entity in model.Entities]
        problems = []
        mapped = [MapSubtypes(EntitySubtree(entity), {index: index for index in range(4096)}) for entity in model.Entities]
        if mapped != [EntitySubtree(entity) for entity in model.Entities]:
            problems.append('identity MapSubtypes changed a subtree')
        chosen = tuple(index for index in range(len(model.Entities)) if index % 2 == 1)
        relinked = RelinkSubtypes(model.Entities, chosen)
        relinks = [signature(WalkSubtypes(EntitySubtree(entity))) for entity in relinked]
        if KTypedCodecs is not None:
            typed_checks(model.Entities, counts, problems)
        rows.append(dict(path=member['path'], member=member['member'], exact=emitted == payload, walk=digest(walks), relink=digest(relinks), problems=problems))
    report['corpus'] = dict(members=len(rows), exact=sum(row['exact'] for row in rows), problems=sum(len(row['problems']) for row in rows), typedCounts=dict(sorted(counts.items())), rows=rows)


def authored(report):
    from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.CreateNurbsBody import CreateNurbsBody
    from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
    from AuthoredModels import authored_models
    from PrepareAcceptance import HISTORY, OUT, STAMP
    rows = []
    for label, model, _ in authored_models():
        journal = CreateNurbsBody(model, HISTORY, STAMP)
        state, history = (OUT / (label + '.smb')).read_bytes(), (OUT / (label + '.smbh')).read_bytes()
        reread = ReadJournal(history)
        rows.append(dict(label=label, historyExact=EmitJournal(journal) == history, stateExact=EmitStateSmb(journal) == state, rereadEqual=reread == journal, reemitExact=EmitJournal(reread) == history, snapshotExact=EmitGeometry(ReadGeometry(state)) == state))
    report['authored'] = rows


def main():
    report = dict(src='production' if Path(OPTIONS.src).resolve() == (ROOT / 'src').resolve() else 'other', typed=KTypedCodecs is not None)
    corpus(report)
    if not OPTIONS.skip_authored:
        authored(report)
    if OPTIONS.base_report:
        base = json.loads(Path(OPTIONS.base_report).read_text())['corpus']['rows']
        pairs = list(zip(base, report['corpus']['rows'], strict=True))
        if any((left['path'], left['member']) != (right['path'], right['member']) for left, right in pairs):
            raise SystemExit('base report lists different members')
        report['base'] = dict(label=OPTIONS.base_label, members=len(pairs), exactEqual=sum(left['exact'] == right['exact'] for left, right in pairs), walkEqual=sum(left['walk'] == right['walk'] for left, right in pairs), relinkEqual=sum(left['relink'] == right['relink'] for left, right in pairs))
    Path(OPTIONS.out).write_text(json.dumps(report, indent=1) + '\n')
    summary = {key: value for key, value in report['corpus'].items() if key != 'rows'}
    print(json.dumps(dict(corpus=summary, authored=report.get('authored'), base=report.get('base')), indent=1))


main()
