"""Write the sanitized native acceptance report for Kit-authored assemblies.

Usage: python3.14 -I MakeAsmAcceptance.py

Reads the private run files under re/Fusion/LocalOracle/LinksConfigs/tmp.
Drops cloud URNs and identifiers. Keeps names, counts, SHA-256 values and checks.
"""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import KUnchangedGuid

oracle = repository / 're/Fusion/LocalOracle/LinksConfigs'
private = oracle / 'tmp'
author = private / 'author'
private_keys = ('lineage_urn', 'version_urn', 'asset_id', 'id', 'urn')


def load(path):
    return json.loads(path.read_text()) if path.exists() else None


def clean(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in private_keys:
                continue
            if key in ('traceback', 'close_errors'):
                text = '\n'.join(item) if isinstance(item, list) else str(item)
                lines = [line for line in text.splitlines() if line.strip()]
                result[key + '_last_line'] = lines[-1] if lines else None
            else:
                result[key] = clean(item)
        return result
    if isinstance(value, list):
        return [clean(item) for item in value]
    return value


def file_row(path):
    data = path.read_bytes()
    return {'name': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def matrices(model):
    found = []

    def walk(value):
        if isinstance(value, MatrixValue):
            found.append(value.Entries)
        elif hasattr(value, '__dataclass_fields__'):
            for key in value.__dataclass_fields__:
                walk(getattr(value, key))
        elif isinstance(value, tuple):
            for item in value:
                walk(item)

    for segment in model.Segments:
        for record in segment.Records:
            walk(record)
    return found


def link_facts(model, targets):
    by_asset = {target.Asset.AssetId: target for target in targets}
    contexts = [context for segment in model.Segments for context in segment.Metadata.Contexts]
    rows = model.Asset.Links
    found = [matrix for matrix in matrices(model)]
    return {
        'links': len(model.Document.Links),
        'contexts_per_segment': [len(segment.Metadata.Contexts) for segment in model.Segments],
        'context_revision_equals_target_document_id': all(
            context.AssetId in by_asset and context.RevisionId == by_asset[context.AssetId].Document.DocumentId for context in contexts
        ),
        'asset_link_snapshot_equals_target_snapshot': all(
            row.AssetId in by_asset and row.SnapshotId == by_asset[row.AssetId].Asset.SnapshotId for row in rows
        ),
        'asset_link_physical_guid_zero': [row.PhysicalGuid == KUnchangedGuid for row in rows],
        'matrix_fields': len(found),
        'empty_matrix_fields': sum(1 for entries in found if entries is None),
    }


def probe_facts(stem, names):
    path = author / (stem + '.f3d')
    if not path.exists():
        return None
    targets = [ReadDocument((author / (name + '.f3d')).read_bytes()) for name in names]
    row = file_row(path)
    row.update(link_facts(ReadDocument(path.read_bytes()), targets))
    return row


def bulk_tails(path):
    rows = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith('BulkStream.dat'):
                continue
            kind = SegmentKind.KAct if 'ACT' in name else SegmentKind.KBrowser if 'Browser' in name else SegmentKind.KDesign
            bulk = archive.read(name)
            spans = ReadBulkSpans(bulk, archive.read(name.replace('BulkStream.dat', 'MetaStream.dat')), Segment=kind)
            rows[kind.name] = {'records': len(spans), 'bytes': len(bulk), 'last_object_continuation': not spans[-1].IsPrimary}
    return rows


def export_facts(path):
    row = file_row(path)
    row['bulk_streams'] = bulk_tails(path)
    try:
        model = ReadDocument(path.read_bytes())
    except ValueError as error:
        row['kit_read'] = False
        row['kit_error'] = str(error)
        return row
    targets = [ReadDocument((author / (name + '.f3d')).read_bytes()) for name in ('KitAsmPartA', 'KitAsmSub')]
    row['kit_read'] = True
    row['links'] = len(model.Document.Links)
    row['contexts_per_segment'] = [len(segment.Metadata.Contexts) for segment in model.Segments]
    row['link_names'] = sorted(dict(link.Properties).get('toDocDisplayName') for link in model.Document.Links)
    return row


def main():
    report = {
        'scope': 'Native Fusion acceptance of Kit EmitAssembly outputs that reference uploaded Kit parts',
        'parts': clean(load(author / 'Parts.json')),
        'assemblies': clean(load(author / 'Assembly.json')),
        'files': [file_row(author / name) for name in ('KitAsmPartA.f3d', 'KitAsmPartB.f3d', 'KitAsmSub.f3d', 'KitAsmRoot.f3d') if (author / name).exists()],
        'uploads': {},
        'probes': {},
        'native_probe_exports': {},
        'acceptance': clean(load(private / 'AcceptAsmRoot.json')),
    }
    for stage in ('parts', 'sub', 'root'):
        value = load(author / f'BeginAsmUpload.{stage}.json')
        if value is not None:
            report['uploads'][stage] = clean(value)
    for stage in ('A', 'B', 'Sub'):
        value = load(author / f'ProbeAsmTargets.{stage}.json')
        if value is not None:
            report['probes'][stage] = clean(value)
    for stem, names in (('ProbeKitAsmPartA', ['KitAsmPartA']), ('ProbeKitAsmPartB', ['KitAsmPartB']), ('ProbeKitAsmSub', ['KitAsmSub', 'KitAsmPartB'])):
        facts = probe_facts(stem, names)
        if facts is not None:
            report['native_probe_exports'][stem] = facts
    report['fusion_exports'] = {}
    for name in ('AcceptedKitAsmRoot', 'ReexportFirstKitAsmRoot', 'ReexportSecondKitAsmRoot'):
        path = author / (name + '.f3d')
        if path.exists():
            report['fusion_exports'][name] = export_facts(path)
    report['reexport'] = clean(load(private / 'ReexportAsmRoot.json'))
    text = json.dumps(report, indent=2) + '\n'
    if str(Path.home()) in text or 'urn:adsk' in text:
        raise SystemExit('private value in acceptance report')
    (oracle / 'AsmAcceptance.json').write_text(text)
    print('sha256', hashlib.sha256(text.encode()).hexdigest())


main()
