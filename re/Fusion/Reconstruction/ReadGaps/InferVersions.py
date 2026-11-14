import itertools
import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from TrySchema import CATALOG, BindProfile, BindRecords, BulkRecord, ExternalTarget, ReadSlack, documents, profile, segments

GAPS = json.loads((BASE.parents[0] / 'ReaderCoverage' / 'ExampleGaps.json').read_text())['gaps']


def cases(guid, version):
    found = []
    for name, data in documents():
        parts = list(segments(data))
        for segment, meta, rows, bulk in parts:
            versions = {row.ClassGuid.upper(): row.SchemaVersion for row in meta.Classes}
            if versions.get(guid.upper()) != version:
                continue
            targets = tuple(
                ExternalTarget(other.Header.SegmentId, oid, row.ClassGuid)
                for _, other, _, _ in parts
                if other.Header.SegmentId != meta.Header.SegmentId
                for row in other.Classes
                for oid in row.OwnerIds
            )
            items = tuple(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, bulk[span.PayloadOffset:span.EndOffset]) for span in rows)
            chosen = [item for span, item in zip(rows, items) if span.ClassGuid.upper() == guid.upper()]
            found.append((name, meta, targets, items, chosen))
    return found


def attempt(found, guid, version, schema, extra):
    table = dict(extra)
    table[(guid.upper(), version)] = schema
    passed = 0
    total = 0
    values = []
    for name, meta, targets, items, chosen in found:
        try:
            catalog = BindProfile(profile(meta, table, targets), meta.Classes)
            scope = BindRecords(items, meta.Classes)
        except Exception:
            return 0, sum(len(entry[4]) for entry in found), []
        for item in chosen:
            total += 1
            try:
                value, slack = ReadSlack(item, scope, catalog)
            except Exception:
                continue
            if not slack:
                passed += 1
                values.append(value)
    return passed, total, values


def candidates(base, depth):
    members = tuple(base.Members)
    saved = [index for index, member in enumerate(members) if member.IsSaved]
    for size in range(depth + 1):
        for removed in itertools.combinations(saved, size):
            kept = tuple(member for index, member in enumerate(members) if index not in removed)
            yield tuple(members[index].FieldName for index in removed), replace(base, Members=kept)


def infer(guid, version, extra, depth=2):
    options = sorted((schema for schema in CATALOG.Classes.get(guid.upper(), ()) if schema.SchemaVersion > version), key=lambda item: item.SchemaVersion)
    found = cases(guid, version)
    results = []
    for base in options:
        for removed, schema in candidates(base, depth):
            schema = replace(schema, SchemaVersion=version)
            passed, total, _ = attempt(found, guid, version, schema, extra)
            if total and passed == total:
                results.append({'from': base.SchemaVersion, 'removed': list(removed), 'records': total})
        if results:
            break
    return results, sum(len(entry[4]) for entry in found)


def main():
    rows = []
    for gap in GAPS:
        if not gap['kind'].startswith('older'):
            continue
        results, total = infer(gap['class_guid'], gap['saved_version'], {}, int(sys.argv[1]) if len(sys.argv) > 1 else 2)
        rows.append({'class': gap['class'], 'version': gap['saved_version'], 'records': total, 'layouts': results})
        print(gap['class'].split('::')[-1], gap['saved_version'], total, json.dumps(results)[:300], flush=True)
    (BASE / 'VersionLayouts.json').write_text(json.dumps(rows, indent=1) + '\n')


if __name__ == '__main__':
    main()
