import collections
import glob
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment
from convert.formats.Fusion.MetaIndex import SegmentKind

PATTERNS = ('re/Fusion/LocalOracle/**/*.f3d', 'tests/**/*.f3d')
FOCUS = BASE / 'SlackFocus.txt'


def corpus():
    paths = set()
    for pattern in PATTERNS:
        paths.update(Path(path) for path in glob.glob(str(ROOT / pattern), recursive=True))
    return sorted(paths)


def streams_exact(data, model):
    original = {stream.SegmentId: stream for stream in ReadContainer(data).Streams}
    for segment in model.Segments:
        emitted = EmitDocSegment(segment)
        source = original.get(emitted.SegmentId)
        if source is None or source.BulkData != emitted.BulkData or source.Metadata != emitted.Metadata:
            return False
    return True


def parts_changed(data, emitted):
    original = {part.Name: part.Payload for part in ReadContainer(data).Parts}
    again = {part.Name: part.Payload for part in ReadContainer(emitted).Parts}
    names = {name for name in set(original) | set(again) if original.get(name) != again.get(name)}
    return sorted({name.split('/')[-2] if '/' in name else name for name in names})


def act_slack(model):
    rows = [segment.BulkSlack for segment in model.Segments if segment.Metadata.Header.Segment is SegmentKind.KAct]
    return rows[0] if len(rows) == 1 else None


def examine(path):
    data = path.read_bytes()
    row = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()}
    try:
        model = ReadDocument(data)
    except ValueError as error:
        row['status'] = 'refused'
        row['message'] = str(error)
        return row
    slack = act_slack(model)
    row['act_slack_bytes'] = None if slack is None else len(slack)
    row['act_slack_sha256'] = None if not slack else hashlib.sha256(slack).hexdigest()
    emitted = EmitParsed(model)
    row['model_equal'] = ReadDocument(emitted) == model
    row['streams_byte_exact'] = streams_exact(data, model)
    row['parts_changed'] = parts_changed(data, emitted)
    row['status'] = 'read'
    return row


def main():
    focus = {line.strip() for line in FOCUS.read_text().splitlines() if line.strip()}
    rows = [examine(path) for path in corpus()]
    chosen = [row for row in rows if row['file'] in focus]
    missing = sorted(focus - {row['file'] for row in chosen})
    summary = collections.Counter()
    for row in rows:
        summary['%s slack=%s equal=%s streams=%s' % (row['status'], bool(row.get('act_slack_bytes')), row.get('model_equal'), row.get('streams_byte_exact'))] += 1
    lengths = collections.Counter(row.get('act_slack_bytes') for row in chosen)
    report = {
        'scope': 'ACT bulk stream slack after the final record; read, re-emit and compare every local archive',
        'python': sys.version.split()[0],
        'focus_archives': len(focus),
        'focus_missing': missing,
        'focus_read': sum(row['status'] == 'read' for row in chosen),
        'focus_model_equal': sum(row.get('model_equal') is True for row in chosen),
        'focus_streams_byte_exact': sum(row.get('streams_byte_exact') is True for row in chosen),
        'focus_parts_changed': collections.Counter(' '.join(row.get('parts_changed', ['refused'])) or 'none' for row in chosen).most_common(),
        'corpus_parts_changed': collections.Counter(' '.join(row['parts_changed']) or 'none' for row in rows if row['status'] == 'read').most_common(),
        'edited_forms': [row for row in rows if row['file'].endswith('Edited.f3d') and '/TSpline/' in row['file']],
        'focus_slack_lengths': {str(key): value for key, value in sorted(lengths.items(), key=lambda item: str(item[0]))},
        'corpus_archives': len(rows),
        'corpus_summary': dict(sorted(summary.items())),
        'refusals': collections.Counter(row['message'] for row in rows if row['status'] == 'refused').most_common(),
        'rows': rows,
    }
    (BASE / 'SlackCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}, indent=1))


if __name__ == '__main__':
    main()
