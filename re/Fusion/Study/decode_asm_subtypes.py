"""Source-ordered ASM inline subtype allocation and guarded backreferences.

Non-ref bracketed definitions consume preorder allocation slots, including
pcurve wrappers and nested inline definitions. Ref blocks consume no slot.
The namespace is blob-local and separate from geometry/global record indices.
"""

import copy
import hashlib
import json
import struct

from asm_records import inspect_asm

SCOPE = ('Observed blob-local source-preorder non-ref subtype allocations and class-compatible prior-definition backreferences; '
         'structural payload reuse only, without persistent topology/native identity or procedural evaluator claims')
ROOTS = {'intcurve-curve': (4, 'curve'), 'spline-surface': (4, 'surface'), 'pcurve': (5, 'pcurve')}
MARKERS = {'intcurve': 'curve', 'spline': 'surface', 'pcurve': 'pcurve'}


def _record_fingerprint(record):
    data = [record['index'], record['name'], record['section'], record['offset'], record['end_offset'],
            [[t['kind'], t['value'], t['offset']] for t in record['tokens']]]
    return hashlib.sha256(json.dumps(data, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def decode_asm_subtypes(blob, *, parsed=None):
    """Return definitions/blocks/references/unresolved; no source mutation.

    Brackets are explicit token boundaries. Unknown class contexts are retained
    and cannot resolve references. Targets must precede and finish before a ref.
    """
    parsed = inspect_asm(blob) if parsed is None else parsed
    if not parsed['complete_token_stream'] or parsed.get('total_bytes') != len(blob):
        raise ValueError('ASM subtype catalog requires a complete matching serialized token stream')
    definitions, blocks = [], []
    for record in parsed['records']:
        stack = []
        ts = record['tokens']
        for i, token in enumerate(ts):
            if token['kind'] == 'subtype_start':
                if i+1 >= len(ts) or ts[i+1]['kind'] != 'entity_name':
                    raise ValueError('ASM subtype bracket has no literal type name')
                name = ts[i+1]['value']
                kind, context = None, None
                root = ROOTS.get(record['name'])
                if not stack and root and i == root[0]:
                    kind, context = root[1], 'Typed top-level '+record['name']+' wrapper'
                elif (i >= 2 and ts[i-1]['kind'] == 'boolean_token'
                      and ts[i-2]['kind'] == 'entity_name' and ts[i-2]['value'] in MARKERS):
                    kind, context = MARKERS[ts[i-2]['value']], 'Literal inline '+ts[i-2]['value']+' wrapper'
                row = {'record_index': record['index'], 'record_kind': record['name'], 'section': record['section'],
                    'token_start': i, 'token_end': None, 'byte_start': token['offset'], 'byte_end': None,
                    'subtype_name': name, 'context_kind': kind, 'context_evidence': context,
                    'parent_definition_index': next((p['definition_index'] for p in reversed(stack) if p['definition_index'] is not None), None),
                    'definition_index': None, 'reference_id': None}
                if name != 'ref':
                    row['definition_index'] = len(definitions)
                    definitions.append(row)
                blocks.append(row)
                stack.append(row)
            elif token['kind'] == 'subtype_end':
                if not stack:
                    raise ValueError('ASM subtype end has no opening bracket')
                row = stack.pop()
                row['token_end'], row['byte_end'] = i, token['offset']+1
                if not (0 <= row['byte_start'] < row['byte_end'] <= len(blob)
                        and blob[row['byte_start']] == 15 and blob[token['offset']] == 16):
                    raise ValueError('ASM subtype token boundaries differ from serialized brackets')
                if row['subtype_name'] == 'ref':
                    start = row['token_start']
                    if i != start+3 or ts[start+2]['kind'] != 'integer':
                        raise ValueError('ASM subtype reference is not an exact ref/integer bracket')
                    value = ts[start+2]['value']
                    if not isinstance(value, int) or isinstance(value, bool):
                        raise ValueError('ASM subtype reference ID is not a typed integer')
                    if (blob[ts[start+2]['offset']] != 4
                            or struct.unpack_from('<q', blob, ts[start+2]['offset']+1)[0] != value):
                        raise ValueError('ASM subtype reference ID differs from serialized integer')
                    row['reference_id'] = value
        if stack:
            raise ValueError('ASM subtype bracket crosses a record boundary')
    references, unresolved = [], []
    for block in blocks:
        if block['subtype_name'] != 'ref':
            continue
        item = dict(block)
        number = item['reference_id']
        reason = None
        target = definitions[number] if 0 <= number < len(definitions) else None
        if target is None:
            reason = 'Inline subtype reference leaves this blob allocation table'
        elif target['byte_end'] > item['byte_start']:
            reason = 'Inline subtype target is forward/open/recursive rather than a complete earlier definition'
        elif item['context_kind'] is None or target['context_kind'] is None:
            reason = 'Inline subtype source or target class context is unqualified'
        elif item['context_kind'] != target['context_kind']:
            reason = 'Inline subtype source/target class contexts disagree'
        if reason:
            item['reason'] = reason
            unresolved.append(item)
        else:
            item.update(target_definition_index=number, target_record_index=target['record_index'],
                        target_token_start=target['token_start'], target_token_end=target['token_end'],
                        target_subtype_name=target['subtype_name'], target_context_kind=target['context_kind'],
                        association='Exact blob-local allocation slot with prior complete bracket and compatible declared wrapper context')
            references.append(item)
    return {'definitions': definitions, 'blocks': blocks, 'references': references, 'unresolved': unresolved,
            'source_blob_sha256': hashlib.sha256(blob).hexdigest(), 'source_total_bytes': len(blob),
            'record_fingerprints': {str(r['index']): _record_fingerprint(r) for r in parsed['records'] if any(t['kind'] == 'subtype_start' for t in r['tokens'])},
            'allocation_rule': 'Each non-ref subtype_start allocates in serialized preorder; ref blocks allocate nothing; nested and pcurve definitions are counted',
            'scope': SCOPE}


def resolve_asm_subtype(catalog, record_index, token_start, *, expected_kind=None):
    """Resolve an exact bracket location, with no coordinate/name fallback."""
    found = [b for b in catalog['blocks'] if b['record_index'] == record_index and b['token_start'] == token_start]
    if len(found) != 1:
        raise ValueError('ASM subtype location is missing or ambiguous')
    source = found[0]
    if expected_kind is not None and source['context_kind'] != expected_kind:
        raise ValueError('ASM subtype caller/source kind disagrees')
    if source['definition_index'] is not None:
        target = source
    else:
        refs = [r for r in catalog['references'] if r['record_index'] == record_index and r['token_start'] == token_start]
        if len(refs) != 1:
            raise ValueError('ASM subtype reference is not independently qualified')
        target = catalog['definitions'][refs[0]['target_definition_index']]
    if target['context_kind'] is None or expected_kind is not None and target['context_kind'] != expected_kind:
        raise ValueError('ASM subtype target kind is unqualified or incompatible')
    return {'source_block': copy.deepcopy(source), 'target_definition': copy.deepcopy(target),
            'source_blob_sha256': catalog['source_blob_sha256'], 'scope': SCOPE}


def expand_asm_subtype_record(record, catalog, records):
    """Opt-in top-level ref payload reuse, retaining original wrapper/trim tail.

    Returns record/provenance. The expanded record is an in-memory decoder input,
    not a new serialized record: payload token offsets retain their source host.
    Non-ref, incompatible, incomplete and unknown contexts raise ValueError.
    """
    if catalog['record_fingerprints'].get(str(record['index'])) != _record_fingerprint(record):
        raise ValueError('ASM reference record is stale or belongs to another subtype catalog')
    root = ROOTS.get(record['name'])
    if root is None:
        raise ValueError('Unsupported ASM subtype reference record class')
    start, kind = root
    resolved = resolve_asm_subtype(catalog, record['index'], start, expected_kind=kind)
    source, target = resolved['source_block'], resolved['target_definition']
    if source['subtype_name'] != 'ref':
        raise ValueError('ASM record is an explicit definition, not a top-level reference')
    hosts = [r for r in records if r['index'] == target['record_index']]
    if len(hosts) != 1:
        raise ValueError('ASM subtype target host is missing or ambiguous')
    host = hosts[0]
    if catalog['record_fingerprints'].get(str(host['index'])) != _record_fingerprint(host):
        raise ValueError('ASM subtype target host is stale or belongs to another catalog')
    if record['tokens'][start+2]['value'] != target['definition_index']:
        raise ValueError('ASM subtype source record differs from its catalog reference ID')
    original_payload = host['tokens'][target['token_start']:target['token_end']+1]
    if (not original_payload or original_payload[0]['kind'] != 'subtype_start'
            or original_payload[-1]['kind'] != 'subtype_end' or original_payload[1]['value'] != target['subtype_name']):
        raise ValueError('ASM subtype target host no longer matches catalog span')
    expanded = copy.deepcopy(record)
    expanded['tokens'] = copy.deepcopy(record['tokens'][:start]+original_payload+record['tokens'][source['token_end']+1:])
    proof = {'is_derived_record': True, 'source_blob_sha256': catalog['source_blob_sha256'], 'referencing_record_index': record['index'],
        'referencing_record_offset': record['offset'], 'referencing_section': record['section'], 'record_kind': record['name'],
        'reference_token_start': start, 'reference_id': target['definition_index'],
        'target_record_index': host['index'], 'target_record_offset': host['offset'], 'target_section': host['section'],
        'target_token_start': target['token_start'], 'target_token_end': target['token_end'],
        'target_payload_byte_start': target['byte_start'], 'target_payload_byte_end': target['byte_end'],
        'target_subtype_name': target['subtype_name'], 'target_context_kind': target['context_kind'],
        'original_wrapper_tokens': copy.deepcopy(record['tokens'][:start]),
        'original_interval_tail_tokens': copy.deepcopy(record['tokens'][source['token_end']+1:]),
        'scope': 'Typed structural payload reuse; referencing wrapper/trim retained, no source wrapper sense or current-state inference'}
    payload_length = len(original_payload)
    proof['token_origins'] = [
        {'role': 'Original referencing wrapper', 'derived_token_start': 0, 'derived_token_end_exclusive': start,
         'source_record_index': record['index'], 'source_token_start': 0, 'source_token_end_inclusive': start-1,
         'source_byte_start': record['tokens'][0]['offset'], 'source_byte_end_exclusive': source['byte_start']},
        {'role': 'Referenced explicit subtype payload', 'derived_token_start': start, 'derived_token_end_exclusive': start+payload_length,
         'source_record_index': host['index'], 'source_token_start': target['token_start'], 'source_token_end_inclusive': target['token_end'],
         'source_byte_start': target['byte_start'], 'source_byte_end_exclusive': target['byte_end']},
        {'role': 'Original referencing outer interval/bounds tail', 'derived_token_start': start+payload_length,
         'derived_token_end_exclusive': len(expanded['tokens']), 'source_record_index': record['index'],
         'source_token_start': source['token_end']+1, 'source_token_end_inclusive': len(record['tokens'])-1,
         'source_byte_start': source['byte_end'], 'source_byte_end_exclusive': record['end_offset']-1}]
    proof['serialization_scope'] = 'Derived in-memory reader input only; source offsets name original hosts and no new serialized record bytes are claimed'
    expanded['is_subtype_expansion'] = True
    expanded['is_derived_record'] = True
    return {'record': expanded, 'provenance': proof}


def decode_asm_subtype_cache(record, catalog, records, *, decoder=None):
    """Optional spline-reader callback; unchanged records use their base reader.

    Only a qualified top-level ref is expanded. A structurally resolved target
    whose cache schema is unsupported still raises from the base decoder.
    """
    if decoder is None:
        from decode_bspline import decode_bspline
        decoder = decode_bspline
    root = ROOTS.get(record['name'])
    ts = record['tokens']
    if root is None or len(ts) <= root[0]+1 or ts[root[0]+1].get('value') != 'ref':
        return decoder(record)
    expanded = expand_asm_subtype_record(record, catalog, records)
    cache = decoder(expanded['record'])
    return {**cache, 'inline_subtype_reference': expanded['provenance']}
