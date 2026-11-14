"""Research census: Form body type and cached tool identity in native archives.

For each local Form archive, record the Body.bodyType, whether every converted
edge has two coedges, the ETCachedTopology.cachedEntityId and the snapshot
serializer's top-entity PassiveIdGenerator.
"""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))

from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import GroupFields  # noqa: E402
from tests.convert.formats.FusionCodec.Documents.Form.FormArchives import KFormArchives  # noqa: E402
from tests.convert.formats.FusionCodec.Documents.Form.GridArchives import KGridArchives, KGridRefusals  # noqa: E402

BODY = 'D3937028-C20C-4E65-B010-94AD418A5C20'
CACHE = 'C46D3EEB-40E1-43FA-83DC-9CB204335417'
SERIALIZER = '40DCC3F41D-E94F-B3B1-3E95-9B6ABE572C'


def primaries(model):
    return {r.ObjectId: r for r in model.Segments[0].Records if r.IsPrimary and r.Groups}


def of_class(records, guid):
    return [GroupFields(r.Groups) for r in records.values() if r.Groups[0].ClassGuid.upper() == guid]


def row(relative, digest):
    payload = (ROOT / relative).read_bytes()
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError(f'{relative} changed')
    model = ReadDocument(payload)
    records = primaries(model)
    history = model.Bodies[0].History
    coedges = [e for e in history.Entities[: history.ActiveCount] if isinstance(e, CoedgeNode)]
    generators = []
    for serializer in of_class(records, SERIALIZER):
        fields = GroupFields(records[serializer['topEntityPIDGenerator'].ObjectId].Groups)
        generators.append({'nextId': fields['nextId'], 'scanOrderIndex': list(fields['scanOrderIndex'].Items), 'top_entity_count': len(fields['addressOfTopEntities'].Items)})
    (body,) = of_class(records, BODY)
    caches = of_class(records, CACHE)
    return {
        'archive': relative,
        'sha256': digest,
        'body_type': body['bodyType'],
        'closed': all(c.Partner >= 0 for c in coedges),
        'cached_entity_ids': [c['cachedEntityId'] for c in caches],
        'top_entity_generators': generators,
    }


def main():
    cases = sorted({(path, digest) for path, digest, *_ in KFormArchives + KGridArchives + KGridRefusals})
    rows = [row(path, digest) for path, digest in cases]
    rule_type = all(r['body_type'] == (2 if r['closed'] else 4) for r in rows)
    rule_cache = all(
        len(r['cached_entity_ids']) == 1
        and [g for g in r['top_entity_generators'] if g['scanOrderIndex'] == r['cached_entity_ids'] and g['nextId'] == r['cached_entity_ids'][0] + 1 and g['top_entity_count'] == 1]
        for r in rows
    )
    report = {
        'scope': 'Body type and cached Form tool identity in local native Form archives',
        'archives': len(rows),
        'body_type_rule': 'bodyType 2 when every coedge has a partner, otherwise 4',
        'body_type_rule_holds': rule_type,
        'cache_identity_rule': 'one ETCachedTopology whose cachedEntityId is the only scanOrderIndex entry of a top-entity generator with nextId cachedEntityId + 1',
        'cache_identity_rule_holds': rule_cache,
        'rows': rows,
    }
    (HERE / 'SolidityCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=1))


if __name__ == '__main__':
    main()
