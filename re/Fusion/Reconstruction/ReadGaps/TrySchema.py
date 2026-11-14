import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ExampleRecords import documents, segments
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.EntityCodec.Records.BindRecords import BindRecords
from convert.formats.Fusion.EntityCodec.Records.ReadEntity import ReadSlack
from convert.formats.Fusion.EntityCodec.Schema.BindProfile import BindProfile
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeRoot import KNativeRoot
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord

CATALOG = DocumentCatalog(ReadDocSchemas())


def pick(guid, version, extra):
    key = (guid.upper(), version)
    if key in extra:
        return extra[key]
    choices = [schema for schema in CATALOG.Classes.get(guid.upper(), ()) if schema.SchemaVersion == version]
    if choices:
        return choices[0]
    return None


def profile(meta, extra, targets=()):
    chosen = {}
    for row in meta.Classes:
        schema = pick(row.ClassGuid, row.SchemaVersion, extra)
        if schema is None:
            schema = ClassSchema(row.ClassGuid.upper(), row.BaseGuid.upper(), row.SchemaVersion, ())
        chosen[row.ClassGuid.upper()] = replace(schema, BaseGuid=row.BaseGuid.upper())
    pending = list(chosen.values())
    while pending:
        schema = pending.pop()
        guids = [schema.BaseGuid.upper()] + [guid for guid in references(schema.Members)]
        for guid in guids:
            if not guid or guid in chosen or guid == KNativeRoot.upper():
                continue
            options = CATALOG.Classes.get(guid, ())
            if options:
                best = max(options, key=lambda item: item.SchemaVersion)
            else:
                best = ClassSchema(guid, KNativeRoot, 0, ())
            chosen[guid] = best
            pending.append(best)
    return EntityProfile(KNativeRoot, tuple(chosen.values()), targets, CATALOG.NamedTypes)


def references(members):
    for member in members:
        yield from wire(member.ValueType)


def wire(value):
    if value.ClassGuid:
        yield value.ClassGuid.upper()
    for argument in value.Arguments:
        yield from wire(argument)
    yield from references(value.Members)


def decode(guid, version, extra, limit=None):
    results = []
    for name, data in documents():
        parts = list(segments(data))
        for segment, meta, rows, bulk in parts:
            targets = tuple(ExternalTarget(other.Header.SegmentId, oid, row.ClassGuid) for _, other, _, _ in parts if other.Header.SegmentId != meta.Header.SegmentId for row in other.Classes for oid in row.OwnerIds)
            versions = {row.ClassGuid.upper(): row.SchemaVersion for row in meta.Classes}
            if versions.get(guid.upper()) != version:
                continue
            prof = profile(meta, extra, targets)
            catalog = BindProfile(prof, meta.Classes)
            items = tuple(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, bulk[span.PayloadOffset:span.EndOffset]) for span in rows)
            scope = BindRecords(items, meta.Classes)
            for span, item in zip(rows, items):
                if span.ClassGuid.upper() != guid.upper():
                    continue
                try:
                    value, slack = ReadSlack(item, scope, catalog)
                    results.append((name, span.ObjectId, span.IsPrimary, len(item.Payload), 'ok' if not slack else f'slack {len(slack)}', value if not slack else slack[:48].hex()))
                except Exception as error:
                    results.append((name, span.ObjectId, span.IsPrimary, len(item.Payload), f'{type(error).__name__}: {error}'[:120], None))
                if limit and len(results) >= limit:
                    return results
    return results
