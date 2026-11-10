"""Framed reciprocal component-scope support value with conditional time rendering.

Four same-document expression contrasts place this stored u64 inside captured
assignment/computation intervals if interpreted as Unix epoch microseconds.
The native schema does not label an epoch, clock, or lifecycle event. Those
interpretations remain explicit hypotheses, separate from typed ownership.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import struct

from decode_assembly import COMPONENT_GUID, component_label
from decode_dependencies import SCOPE_GUID, scope_datum
from decode_sketch import reference

SUPPORT_GUID = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
SCOPE = ('Exact39-byte reciprocal component-scope support framing and raw u64; '
         'UTC rendering conditional on epoch-microsecond interpretation; lifecycle event unknown')


def decode_scope_update_times(data, records, assembly):
    """Return decoded/unresolved/scope using existing typed component/scope routes.

    assembly is the existing decode_assembly summary. No feature-dependency,
    parameter-expression, or wall-clock edge is synthesized by this reader.
    """
    records = list(records)
    primary, definitions, components = {}, {}, {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)
        if record.class_guid == COMPONENT_GUID:
            definitions.setdefault(record.object_id, []).append(record)
    for component in assembly.get('components', []):
        components.setdefault(component['object_id'], []).append(component)
    decoded, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != SCOPE_GUID:
            continue
        try:
            if len(primary.get(record.object_id, [])) != 1:
                raise ValueError('Component-scope primary identity is ambiguous')
            body = data[record.body:record.end]
            component_id = reference(body, 3)
            choices = definitions.get(component_id, [])
            summaries = components.get(component_id, [])
            if len(choices) != 1 or len(summaries) != 1:
                raise ValueError('Scope component definition/summary is absent or ambiguous')
            definition = choices[0]
            label = component_label(data[definition.body:definition.end], component_id)
            if any(summaries[0].get(key) != value for key, value in label.items()):
                raise ValueError('Scope component summary disagrees with typed component definition')
            scope = scope_datum(body, record.object_id, {component_id: label})
            anchors = primary.get(scope['anchor_object_id'], [])
            if len(anchors) != 1 or anchors[0].class_guid != SUPPORT_GUID:
                raise ValueError('Scope anchor is not one typed support primary')
            anchor = anchors[0]
            support = data[anchor.body:anchor.end]
            if len(support) != 39 or support[:12] != bytes(12) or support[31:] != bytes(8):
                raise ValueError('Unsupported reciprocal scope support framing')
            if reference(support, 12) != record.object_id:
                raise ValueError('Scope support backlink disagrees with scope owner')
            stored = struct.unpack_from('<Q', support, 23)[0]
            utc = None
            status = 'Zero retained without an epoch date or an unset-event claim'
            if stored:
                try:
                    utc = (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=stored)).isoformat(timespec='microseconds')
                    status = 'Conditional conversion only; epoch and unit inferred from captured journal contrasts'
                except (OverflowError, ValueError):
                    status = 'Raw u64 retained; conditional epoch-microsecond conversion exceeds datetime range'
            decoded.append(dict(scope, support_object_id=anchor.object_id,
                support_class_guid=anchor.class_guid, component_class_guid=definition.class_guid,
                stored_u64=stored, stored_u64_relative_offset=23,
                derived_UTC_if_epoch_microseconds=utc, time_interpretation_status=status,
                specific_lifecycle_event=None, native_clock_epoch_and_unit=None,
                source_support_payload_byte_count=39,
                source_support_payload_sha256=hashlib.sha256(support).hexdigest(),
                ownership_status='Typed scope component and anchor references; support reciprocally references this scope',
                scope=SCOPE))
        except (ValueError, IndexError, KeyError, struct.error) as error:
            unresolved.append(dict(object_id=record.object_id, class_guid=record.class_guid, reason=str(error)))
    return dict(decoded=decoded, unresolved=unresolved, scope=SCOPE)
