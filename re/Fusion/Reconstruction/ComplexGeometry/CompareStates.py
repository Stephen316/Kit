"""Compare EmitStateSmb output with the archive snapshot of each corpus history.

Run with /opt/homebrew/bin/python3.14 -I (ZIP method 93 needs Python 3.14).
Writes CompareStates.json next to this script. Paths in the output are repository relative.

Each snapshot body is compared with every body of every retained history state under four
modes. A body comparison follows references from the body record in breadth-first token order,
so it does not depend on the stream order of the records.

- exact: every record field is equal.
- entity tags cleared: the entity tag of every record is set to -1 on both sides.
- snapshot rule: entity tags cleared, and TimeAttrib and TagAttrib records owned by a body and
  every TrackAttrib record are removed, with the attribute chains spliced.
- all attributes removed: entity tags cleared, and every attribute record is removed.

When a snapshot holds only history bodies, the script also rebuilds the snapshot bytes from the
history. It applies the snapshot rule to the matching state and writes the records in one
breadth-first order from all body roots.
"""
import collections
import dataclasses
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.TcoedgeNode import TcoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.RelinkSubtypes import RelinkSubtypes  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import ReadEntityNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import GeometryState  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.SnapshotForm import SnapshotForm  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import MakeEntityNode  # noqa: E402
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord  # noqa: E402

ATTRIBUTES = ('TimeAttrib', 'TrackAttrib', 'TagAttrib', 'SketchAttrib', 'StitchAttrib', 'VertedgeAttrib')
MODES = ('exact', 'entity tags cleared', 'snapshot rule', 'all attributes removed')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def is_attribute(value):
    return type(value).__name__ in ATTRIBUTES


class Table:
    """Records of one entity list with the per-mode attribute splices."""

    def __init__(self, entities):
        self.entities = entities
        self.records = [MakeEntityNode(value) for value in entities]
        self.splices = {}

    def dropped(self, mode):
        if mode in ('exact', 'entity tags cleared'):
            return frozenset()
        if mode == 'all attributes removed':
            return frozenset(index for index, value in enumerate(self.entities) if is_attribute(value))
        result = set()
        for index, value in enumerate(self.entities):
            if isinstance(value, TrackAttrib):
                result.add(index)
            elif isinstance(value, (TimeAttrib, TagAttrib)) and isinstance(self.entities[value.Links.OwnerRef], BodyNode):
                result.add(index)
        return frozenset(result)

    def splice(self, mode):
        if mode in self.splices:
            return self.splices[mode]
        drop = self.dropped(mode)
        override = {}
        if drop:
            for index, record in enumerate(self.records):
                if index == 0 or index in drop:
                    continue
                head = record.Tokens[0][1]
                if not (isinstance(head, int) and head > 0):
                    continue
                chain, seen, current = [], set(), head
                while isinstance(current, int) and current > 0 and current not in seen:
                    seen.add(current)
                    chain.append(current)
                    current = self.records[current].Tokens[2][1]
                kept = [item for item in chain if item not in drop]
                if len(kept) == len(chain):
                    continue
                override[(index, 0)] = kept[0] if kept else -1
                for ordinal, item in enumerate(kept):
                    override[(item, 2)] = kept[ordinal + 1] if ordinal + 1 < len(kept) else -1
                    override[(item, 3)] = kept[ordinal - 1] if ordinal > 0 else -1
        self.splices[mode] = (drop, override)
        return self.splices[mode]

    def refs(self, index, mode):
        drop, override = self.splice(mode)
        result = []
        for slot, (tag, field) in enumerate(self.records[index].Tokens):
            if tag == 12 and isinstance(field, int) and field >= 0:
                value = override.get((index, slot), field)
                result.append((slot, -1 if value in drop else value))
        return result

    def order(self, roots, mode):
        drop, _ = self.splice(mode)
        seen = set(roots)
        queue = collections.deque(roots)
        result = []
        while queue:
            index = queue.popleft()
            result.append(index)
            for _, target in self.refs(index, mode):
                if target > 0 and target not in seen and target not in drop:
                    seen.add(target)
                    queue.append(target)
        return result

    def tokens(self, index, record, mode, mapping):
        refs = dict(self.refs(index, mode))
        tokens = []
        for slot, (tag, field) in enumerate(record.Tokens):
            if slot in refs:
                target = refs[slot]
                tokens.append((tag, mapping.get(target, -1) if target > 0 else target))
            elif mode != 'exact' and slot == 1 and tag == 4:
                tokens.append((tag, -1))
            else:
                tokens.append((tag, field))
        return tuple(tokens)

    def canonical(self, body, mode):
        order = self.order([body], mode)
        mapping = {index: ordinal for ordinal, index in enumerate(order)}
        mapping[0] = 'root'
        relinked = RelinkSubtypes(self.entities, tuple(order))
        return tuple((self.records[index].Name, self.tokens(index, MakeEntityNode(value), mode, mapping)) for index, value in zip(order, relinked))

    def serialize(self, roots, mode):
        order = [0, *self.order(list(roots), mode)]
        mapping = {index: ordinal for ordinal, index in enumerate(order)}
        relinked = RelinkSubtypes(self.entities, tuple(order))
        return tuple(ReadEntityNode(AsmRecord(self.records[index].Name, self.tokens(index, MakeEntityNode(value), mode, mapping))) for index, value in zip(order, relinked))


def root_list(table):
    """Records that no earlier record references, in stream order."""
    referenced, roots = set(), []
    for index in range(1, len(table.entities)):
        if index not in referenced:
            roots.append(index)
        for _, target in table.refs(index, 'exact'):
            if target > index:
                referenced.add(target)
    return roots


def surface_forms(table, body):
    forms = []
    for index in table.order([body], 'exact'):
        value = table.entities[index]
        if isinstance(value, FaceNode):
            record = MakeEntityNode(RelinkSubtypes(table.entities, (value.Surface,))[0])
            forms.append((record.Name, record.Tokens[2:]))
    return forms


def bodies(entities):
    return [index for index, value in enumerate(entities) if isinstance(value, BodyNode)]


def coedge_edge(value):
    if isinstance(value, CoedgeNode):
        return value.EdgeRef
    if isinstance(value, TcoedgeNode):
        return value.Base.EdgeRef
    return None


def describe_body(table, body):
    order = table.order([body], 'exact')
    entities = table.entities
    kinds = collections.Counter(type(entities[index]).__name__ for index in order)
    faces = [entities[index] for index in order if isinstance(entities[index], FaceNode)]
    uses = collections.Counter(coedge_edge(entities[index]) for index in order if coedge_edge(entities[index]) is not None)
    closed = bool(uses) and all(count == 2 for count in uses.values()) and not any(face.DoubleSided for face in faces)
    return dict(
        bodyIndex=body,
        kind='solid' if closed else 'sheet',
        faces=kinds['FaceNode'],
        shells=kinds['ShellNode'],
        edges=kinds['EdgeNode'],
        splineFaces=kinds['SplineNode'],
        transform=kinds['TransformNode'] > 0,
        attributes={name: kinds[name] for name in ATTRIBUTES if kinds[name]},
        records=len(order),
    )


def attribute_payload(table, index):
    record = table.records[index]
    tokens = record.Tokens[5:]
    label = tokens[0][1] if tokens and tokens[0][0] == 7 else ''
    return type(table.entities[index]).__name__, str(label), repr(tokens)


def attribute_chain(table, owner):
    chain, seen = [], set()
    current = table.records[owner].Tokens[0][1]
    while isinstance(current, int) and current > 0 and current not in seen:
        seen.add(current)
        chain.append(current)
        current = table.records[current].Tokens[2][1]
    return chain


def aligned_differences(snapshot, snapshot_body, state, state_body):
    first = snapshot.order([snapshot_body], 'all attributes removed')
    second = state.order([state_body], 'all attributes removed')
    state_only, snapshot_only, tags = collections.Counter(), collections.Counter(), collections.Counter()
    for left, right in zip(first, second):
        owner = snapshot.records[left].Name
        ours = collections.Counter(attribute_payload(snapshot, index) for index in attribute_chain(snapshot, left))
        theirs = collections.Counter(attribute_payload(state, index) for index in attribute_chain(state, right))
        for (kind, label, _), count in (theirs - ours).items():
            state_only[(owner, kind, label)] += count
        for (kind, label, _), count in (ours - theirs).items():
            snapshot_only[(owner, kind, label)] += count
        left_tag, right_tag = snapshot.records[left].Tokens[1][1], state.records[right].Tokens[1][1]
        if left_tag != right_tag:
            tags[(owner, left_tag, 'set' if right_tag >= 0 else right_tag)] += 1
    pack = lambda counter, names: [dict(zip(names, key), count=count) for key, count in sorted(counter.items(), key=str)]
    return dict(
        stateOnlyAttributes=pack(state_only, ('owner', 'type', 'definition')),
        snapshotOnlyAttributes=pack(snapshot_only, ('owner', 'type', 'definition')),
        entityTags=pack(tags, ('owner', 'snapshotTag', 'stateTag')),
    )


def short(value, limit=160):
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + '...'


def first_difference(snapshot, emitted):
    for index, (left, right) in enumerate(zip(snapshot, emitted)):
        if left == right:
            continue
        if type(left) is not type(right):
            return dict(index=index, snapshot=type(left).__name__, state=type(right).__name__, fields='record kinds differ')
        fields = [field.name for field in dataclasses.fields(left) if getattr(left, field.name) != getattr(right, field.name)]
        return dict(index=index, snapshot=type(left).__name__, state=type(right).__name__, fields=', '.join(fields), snapshotValue=short([getattr(left, name) for name in fields]), stateValue=short([getattr(right, name) for name in fields]))
    if len(snapshot) != len(emitted):
        return dict(index=min(len(snapshot), len(emitted)), snapshot=len(snapshot), state=len(emitted), fields='record counts differ')
    return None


def assign(pairs):
    """Assign snapshot bodies to state bodies one to one, strictest mode first."""
    result = {}
    taken = set()
    for mode_index, snapshot_body, state_body in sorted(pairs):
        if snapshot_body in result or state_body in taken:
            continue
        result[snapshot_body] = (state_body, mode_index)
        taken.add(state_body)
    return result


def compare(path):
    with zipfile.ZipFile(ROOT / path) as archive:
        names = archive.namelist()
        histories = [name for name in names if name.endswith('.smbh')]
        snapshots = [name for name in names if name.endswith('.smb')]
        if len(histories) != 1 or len(snapshots) != 1:
            return None
        history_bytes, snapshot_bytes = archive.read(histories[0]), archive.read(snapshots[0])
    journal = ReadJournal(history_bytes)
    snapshot_state = ReadGeometry(snapshot_bytes)
    current_id = journal.Stream.CurrentStateId
    emitted_bytes = EmitStateSmb(journal)
    emitted = ReadGeometry(emitted_bytes)
    states = {}
    for live in Materialize(journal):
        try:
            states[live.StateId] = Table(ReadGeometry(EmitStateSmb(journal, live.StateId)).Entities)
        except ValueError:
            continue
    if current_id not in states:
        raise RuntimeError('Current state has no live body')
    snapshot = Table(snapshot_state.Entities)
    snapshot_bodies = bodies(snapshot.entities)
    forms = {}
    for state_id, table in states.items():
        for body in bodies(table.entities):
            for mode in MODES:
                forms.setdefault(table.canonical(body, mode), []).append((state_id, body, mode))
    pairs = collections.defaultdict(list)
    for body in snapshot_bodies:
        for mode_index, mode in enumerate(MODES):
            for state_id, state_body, state_mode in forms.get(snapshot.canonical(body, mode), []):
                if state_mode == mode:
                    pairs[state_id].append((mode_index, body, state_body))
    assigned = {state_id: assign(pairs[state_id]) for state_id in states}
    rows = []
    for body in snapshot_bodies:
        row = describe_body(snapshot, body)
        candidates = [(assigned[state_id][body][1], state_id) for state_id in states if body in assigned[state_id]]
        row['match'] = None
        if not candidates:
            loose = [(mode, state_id, state_body) for state_id in states for mode, snapshot_body, state_body in pairs[state_id] if snapshot_body == body]
            if loose:
                best = min(mode for mode, _, _ in loose)
                state_ids = sorted({state_id for mode, state_id, _ in loose if mode == best})
                target = current_id if current_id in state_ids else state_ids[-1]
                target_body = min(state_body for mode, state_id, state_body in loose if mode == best and state_id == target)
                owner = next(snapshot_body for snapshot_body, (state_body, _) in assigned[target].items() if state_body == target_body)
                row['match'] = dict(mode=MODES[best], stateIds=state_ids, comparedState=target, comparedBody=target_body, duplicateOfSnapshotBody=owner)
                if best > 0:
                    row['match'].update(aligned_differences(snapshot, body, states[target], target_body))
        if candidates:
            best = min(mode for mode, _ in candidates)
            state_ids = sorted(state_id for mode, state_id in candidates if mode == best)
            target = current_id if current_id in state_ids else state_ids[-1]
            target_body = assigned[target][body][0]
            row['match'] = dict(mode=MODES[best], stateIds=state_ids, comparedState=target, comparedBody=target_body)
            if best > 0:
                row['match'].update(aligned_differences(snapshot, body, states[target], target_body))
        rows.append(row)
    current_surfaces = collections.Counter(form for body in bodies(states[current_id].entities) for form in surface_forms(states[current_id], body))
    for row in rows:
        if row['match'] is None:
            forms = surface_forms(snapshot, row['bodyIndex'])
            row['surfacesInCurrentState'] = dict(equal=sum(form in current_surfaces for form in forms), total=len(forms), splineEqual=sum(form in current_surfaces for form in forms if form[0] == 'spline-surface'), splineTotal=sum(form[0] == 'spline-surface' for form in forms))
    roots = root_list(snapshot)
    current_rows = []
    held = {assigned[current_id][body][0] for body in snapshot_bodies if body in assigned[current_id]}
    for body in bodies(states[current_id].entities):
        row = describe_body(states[current_id], body)
        row['inSnapshot'] = body in held
        current_rows.append(row)
    history_bodies = [row['bodyIndex'] for row in rows if row['match'] is not None and 'duplicateOfSnapshotBody' not in row['match']]
    holding = sorted(state_id for state_id in states if history_bodies and all(body in assigned[state_id] for body in history_bodies))
    entry = dict(
        path=path,
        historyMember=histories[0],
        snapshotMember=snapshots[0],
        historySha256=digest(history_bytes),
        snapshotSha256=digest(snapshot_bytes),
        emittedSha256=digest(emitted_bytes),
        bytesEqual=emitted_bytes == snapshot_bytes,
        entitiesEqual=emitted.Entities == snapshot_state.Entities,
        snapshotRecords=len(snapshot.entities),
        emittedRecords=len(emitted.Entities),
        snapshotEntityTags=sorted({record.Tokens[1][1] for record in snapshot.records[1:]}),
        snapshotRoots=dict(collections.Counter(snapshot.records[index].Name for index in roots)),
        snapshotRootsLead=roots == list(range(1, len(roots) + 1)),
        snapshotBreadthFirst=snapshot.serialize(roots, 'exact') == snapshot_state.Entities,
        snapshotFormFixedPoint=SnapshotForm(snapshot_state.Entities) == snapshot_state.Entities,
        stampEqual=emitted.Stamp == snapshot_state.Stamp,
        headerDifferences={field.name: [getattr(snapshot_state.Header, field.name), getattr(emitted.Header, field.name)] for field in dataclasses.fields(emitted.Header) if getattr(snapshot_state.Header, field.name) != getattr(emitted.Header, field.name)},
        firstDifference=first_difference(snapshot_state.Entities, emitted.Entities),
        currentStateId=current_id,
        retainedStates={str(state_id): len(bodies(states[state_id].entities)) for state_id in sorted(states)},
        statesHoldingAllHistoryBodies=holding,
        snapshotBodies=rows,
        currentBodies=current_rows,
    )
    entry['rebuild'] = rebuild(entry, states, assigned, snapshot_bytes, snapshot_state, journal)
    entry['differenceClass'] = classify(entry)
    return entry


def rebuild(entry, states, assigned, snapshot_bytes, snapshot_state, journal):
    rows = entry['snapshotBodies']
    if any(row['match'] is None for row in rows) or not entry['statesHoldingAllHistoryBodies']:
        return None
    state_id = entry['statesHoldingAllHistoryBodies'][-1]
    table = states[state_id]
    if len(bodies(table.entities)) != len(rows):
        return dict(stateId=state_id, status='state holds other bodies')
    mapping = assigned[state_id]
    result = dict(stateId=state_id, mode='snapshot rule')
    if any(MODES[mode] not in ('exact', 'entity tags cleared', 'snapshot rule') for _, mode in mapping.values()):
        result['status'] = 'a body needs more than the snapshot rule'
        return result
    for label, roots in (('stateBodyOrder', bodies(table.entities)), ('snapshotBodyOrder', [mapping[row['bodyIndex']][0] for row in rows])):
        entities = table.serialize(roots, 'snapshot rule')
        header = dataclasses.replace(snapshot_state.Header, RootCount=len(roots) + 1)
        payload = EmitGeometry(GeometryState(header, journal.Stamp, entities))
        result[label] = dict(sha256=digest(payload), bytesEqual=payload == snapshot_bytes, entitiesEqual=entities == snapshot_state.Entities)
    production = EmitStateSmb(journal, state_id, Snapshot=True)
    result['production'] = dict(call='EmitStateSmb(journal, stateId, Snapshot=True)', sha256=digest(production), bytesEqual=production == snapshot_bytes)
    result['status'] = 'rebuilt'
    return result


def classify(entry):
    rows = entry['snapshotBodies']
    current = entry['currentStateId']
    holding = entry['statesHoldingAllHistoryBodies']
    outside = [row for row in rows if row['match'] is None]
    missing = sum(not row['inSnapshot'] for row in entry['currentBodies'])
    if not holding:
        head = 'no single state holds the history bodies'
    elif holding[-1] == current:
        head = 'current state'
    else:
        head = 'earlier state'
    parts = [head + (' with every current body' if missing == 0 else ' without some current bodies' if head == 'current state' else '')]
    kinds = sorted({row['kind'] for row in outside})
    if any(row['match'] and 'duplicateOfSnapshotBody' in row['match'] for row in rows):
        parts.append('plus a second copy of a history body')
    if kinds:
        parts.append('plus ' + ' and '.join(kind + ' bodies' for kind in kinds) + ' outside the history')
    return ', '.join(parts)


def authored_fixtures():
    folder = ROOT / 're/Fusion/LocalOracle/ComplexGeometry'
    result = {}
    for history in sorted(folder.glob('Authored*.smbh')):
        payload = EmitStateSmb(ReadJournal(history.read_bytes()))
        result[history.stem] = dict(sha256=digest(payload), equalsCommittedSmb=payload == history.with_suffix('.smb').read_bytes())
    return result


def selection():
    verify = json.loads((HERE / 'VerifyComplex.json').read_text())
    return sorted({item['path'] for item in verify['members'] if item.get('exact') and item['member'].endswith('.smbh')})


def main():
    rows = []
    for path in selection():
        entry = compare(path)
        if entry is None:
            continue
        rows.append(entry)
        print(entry['differenceClass'], '|', path, '|', entry['rebuild'], flush=True)
    classes = collections.Counter(entry['differenceClass'] for entry in rows)
    modes = collections.Counter((body['match']['mode'] + (', duplicate of another snapshot body' if 'duplicateOfSnapshotBody' in body['match'] else '')) if body['match'] else 'not in any retained state' for entry in rows for body in entry['snapshotBodies'])
    outside = collections.Counter(f"{body['kind']}, {body['faces']} faces, {'with' if body['attributes'].get('SketchAttrib') else 'without'} SketchAttrib" for entry in rows for body in entry['snapshotBodies'] if body['match'] is None)
    state_only, snapshot_only, tags = collections.Counter(), collections.Counter(), collections.Counter()
    for entry in rows:
        for body in entry['snapshotBodies']:
            match = body['match']
            if not match or match['mode'] == 'exact':
                continue
            for item in match['stateOnlyAttributes']:
                state_only[f"{item['owner']} {item['type']} {item['definition']}"] += item['count']
            for item in match['snapshotOnlyAttributes']:
                snapshot_only[f"{item['owner']} {item['type']} {item['definition']}"] += item['count']
            for item in match['entityTags']:
                tags[f"{item['owner']} snapshot {item['snapshotTag']} state {item['stateTag']}"] += item['count']
    rebuilt = [entry['rebuild'] for entry in rows if entry['rebuild'] and entry['rebuild'].get('status') == 'rebuilt']
    summary = dict(
        archives=len(rows),
        bytesEqual=sum(entry['bytesEqual'] for entry in rows),
        entitiesEqual=sum(entry['entitiesEqual'] for entry in rows),
        stampEqual=sum(entry['stampEqual'] for entry in rows),
        snapshotEntityTagsAllCleared=sum(entry['snapshotEntityTags'] == [-1] for entry in rows),
        headerDifferenceFields=dict(collections.Counter(field for entry in rows for field in entry['headerDifferences'])),
        classes=dict(classes.most_common()),
        snapshotBodies=sum(len(entry['snapshotBodies']) for entry in rows),
        snapshotBodyMatches=dict(modes.most_common()),
        bodiesOutsideHistory=dict(outside.most_common()),
        stateOnlyAttributes=dict(state_only.most_common()),
        snapshotOnlyAttributes=dict(snapshot_only.most_common()),
        entityTagDifferences=dict(tags.most_common()),
        currentBodies=sum(len(entry['currentBodies']) for entry in rows),
        currentBodiesInSnapshot=sum(body['inSnapshot'] for entry in rows for body in entry['currentBodies']),
        rebuildAttempts=len(rebuilt),
        rebuiltBytesEqual={label: sum(item[label]['bytesEqual'] for item in rebuilt) for label in ('stateBodyOrder', 'snapshotBodyOrder', 'production')},
        snapshotRootKinds=dict(collections.Counter(', '.join(sorted(entry['snapshotRoots'])) for entry in rows)),
        snapshotRootsLead=sum(entry['snapshotRootsLead'] for entry in rows),
        snapshotBreadthFirst=sum(entry['snapshotBreadthFirst'] for entry in rows),
        snapshotFormFixedPoint=sum(entry['snapshotFormFixedPoint'] for entry in rows),
        outsideSurfacesInCurrentState=dict(collections.Counter(f"{body['kind']}: {body['surfacesInCurrentState']['equal']} of {body['surfacesInCurrentState']['total']} surfaces, {body['surfacesInCurrentState']['splineEqual']} of {body['surfacesInCurrentState']['splineTotal']} spline" for entry in rows for body in entry['snapshotBodies'] if body['match'] is None and body['kind'] == 'solid')),
        outsideSheetSurfacesInCurrentState=sum(body['surfacesInCurrentState']['equal'] == body['surfacesInCurrentState']['total'] for entry in rows for body in entry['snapshotBodies'] if body['match'] is None and body['kind'] == 'sheet'),
        authoredFixtures=authored_fixtures(),
    )
    (HERE / 'CompareStates.json').write_text(json.dumps(dict(schema='FusionStateSnapshotComparison/2', modes=list(MODES), summary=summary, archives=rows), indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
