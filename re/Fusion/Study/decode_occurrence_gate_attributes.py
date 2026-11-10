"""Strict opt-in imported root occurrence with three typed stored attributes.

Attribute names/values are retained literally. Their activation, visibility,
gating and resolution semantics have not been independently varied or decoded.
Ordinary occurrences use the unchanged existing parser and output exactly.
"""

import struct
import uuid

from decode_assembly import occurrence
from decode_placement import IDENTITY
from decode_sketch import ascii_string, same
from fusion_metadata import Reader

EXPECTED = (
    ('GatedByParent','IntrinsicMetaTypebool'),
    ('ResolutionTime','IntrinsicMetaTypeHString'),
    ('SelfGated','IntrinsicMetaTypebool'),
)


def occurrence_with_gate_attributes(payload, identity):
    """Callback(full raw occurrence payload, object_id) -> canonical occurrence.

    Try the standard parser first. The extension admits only the captured root,
    ordered3-attribute/false-empty-false form with an identity root transform.
    It consumes typed fields and delegates a read-only normalized payload to the
    existing suffix parser; no native file is rewritten or regenerated.
    """
    try:
        return occurrence(payload,identity)
    except (ValueError,IndexError,UnicodeError,struct.error):
        pass
    reader=Reader(payload)
    if reader.string()!='rootInstance':
        raise ValueError('Only captured attributed root occurrence supported')
    chunk_start=reader.position
    chunk=payload[chunk_start:]
    if chunk[:5]!=bytes.fromhex('0101000000') or chunk[16:21]!=bytes(4)+b'\1':
        raise ValueError('Unsupported attributed root occurrence prefix')
    count=struct.unpack_from('<I',chunk,21)[0]
    if count!=3:
        raise ValueError('Only captured three-entry root attribute table supported')
    cursor=25
    attributes=[]
    for key,kind in EXPECTED:
        attribute_start=cursor
        stored_key,cursor=ascii_string(chunk,cursor)
        stored_kind,cursor=ascii_string(chunk,cursor)
        if (stored_key,stored_kind)!=(key,kind):
            raise ValueError('Unobserved root occurrence attribute name/type/order')
        if kind=='IntrinsicMetaTypebool':
            if chunk[cursor:cursor+1]!=b'\0':
                raise ValueError('Uncaptured nonzero root gate attribute value')
            value=False
            raw=chunk[cursor:cursor+1]
            cursor+=1
        else:
            # Only the empty HString payload is observed; no text encoding or
            # nonempty-string layout is inferred from four zero bytes.
            if chunk[cursor:cursor+4]!=bytes(4):
                raise ValueError('Only captured empty root HString payload supported')
            value=None
            raw=chunk[cursor:cursor+4]
            cursor+=4
        attributes.append({'name':key,'stored_type':kind,'stored_bool':value if kind.endswith('bool') else None,
                           'empty_hstring_payload':True if kind.endswith('HString') else None,
                           'raw_value_hex':raw.hex(),'payload_relative_offset':chunk_start+attribute_start})
    if cursor!=157:
        raise ValueError('Unobserved root occurrence attribute-table extent')
    normalized=payload[:chunk_start]+chunk[:21]+bytes(4)+chunk[cursor:]
    result=occurrence(normalized,identity)
    if (result['parent_collection_object_id'] is not None or result['instance_number']!=0
            or result['explicit_name']!='rootInstance' or not same(result['local_transform'],IDENTITY)):
        raise ValueError('Attributed occurrence does not match captured identity document root')
    for field in ('namespace_text','instance_guid_text'):
        uuid.UUID(result[field])
    result.update(stored_occurrence_attributes=attributes,
                  stored_attribute_table_payload_offset=chunk_start+21,
                  stored_attribute_table_length=cursor-21,
                  attribute_schema_status='Typed literal names and false/empty values only; activation, gating, visibility and resolution semantics unresolved',
                  occurrence_schema_status='Captured imported identity root attribute table plus unchanged canonical occurrence suffix framing')
    return result
