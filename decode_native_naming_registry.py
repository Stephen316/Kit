"""Stored native owner/opaque naming-key tables in the observed registry.

Naming keys never become native Design object IDs. Owner fields are resolved
independently to unique typed native records, and a typed footer/backlink binds
the registry to its owning native history container.
"""
import struct

from decode_sketch import reference

REGISTRY = '5D89B935-3F04-4CAB-81F5-E7B309E7E13F'
OWNER = 'C3423E04-7E85-4B44-8E31-A5FA9C100052'
SCOPE = ('Observed reciprocal owner-to-naming-key and key-to-owner tables with typed native owner records '
         'and registry-container backlink. Keys are opaque naming literals, not native object IDs, '
         'ASM entity ordinals, lifecycle classes or complete persistent topology identifiers.')

REVERSE_ONLY_SCOPE = ('Observed stored reverse-only naming-key/typed-native-owner table with an explicit empty forward table '
                      'and exact registry-container footer/backlink. No missing forward rows are synthesized; '
                      'bidirectional reciprocity, persistent topology identity and lifecycle remain unclaimed.')


def encode_native_naming_registry(registry):
    """Exact observed payload replay, preserving both table orders."""
    out = bytearray(b'\0\0'+struct.pack('<I',len(registry['owner_to_keys'])))
    for row in registry['owner_to_keys']:
        out.extend(struct.pack('<QI',row['native_owner_object_id'],len(row['naming_keys'])))
        for key in row['naming_keys']:
            out.extend(struct.pack('<Q',key))
    out.extend(struct.pack('<I',len(registry['key_to_owner'])))
    for row in registry['key_to_owner']:
        out.extend(struct.pack('<QQ',row['naming_key'],row['native_owner_object_id']))
    out.extend(bytes.fromhex(registry['stored_footer_hex']))
    return bytes(out)


def decode_native_naming_registry(data,records):
    """Return decoded/unresolved/scope without touching source records."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id,[]).append(record)
    primary = {i:rows[0]for i,rows in grouped.items()if len(rows)==1}
    result = {'decoded':[],'unresolved':[],'scope':SCOPE}
    for record in records:
        if not record.is_primary or record.class_guid!=REGISTRY:
            continue
        try:
            if primary.get(record.object_id)is not record:
                raise ValueError('Native naming registry object identity is ambiguous')
            body=data[record.body:record.end]
            if len(body)<21 or body[:2]!=bytes(2):
                raise ValueError('Unobserved native naming registry prefix/extent')
            cursor=2
            def number(fmt):
                nonlocal cursor
                width=struct.calcsize(fmt)
                if cursor+width>len(body):
                    raise ValueError('Truncated native naming registry counted extent')
                value,=struct.unpack_from(fmt,body,cursor);cursor+=width
                return value
            count=number('<I')
            if not 0<=count<=100000:
                raise ValueError('Native naming owner count unsupported')
            forward,owned_keys,owner_ids=[],{},set()
            for _ in range(count):
                owner_offset=record.body+cursor
                owner,n=number('<Q'),number('<I')
                target=primary.get(owner)
                if target is None or owner in owner_ids or owner==record.object_id or not 1<=n<=100000:
                    raise ValueError('Native naming owner reference/count is missing, ambiguous or duplicated')
                owner_ids.add(owner)
                if cursor+8*n>len(body)-19 or len(owned_keys)+n>1000000:
                    raise ValueError('Native naming key extent exceeds bounded payload')
                keys,offsets=[],[]
                for _ in range(n):
                    offsets.append(record.body+cursor)
                    key=number('<Q')
                    if not 1<=key<=0x7fffffff or key in owned_keys:
                        raise ValueError('Native naming key invalid or owned more than once')
                    keys.append(key);owned_keys[key]=owner
                forward.append({'native_owner_object_id':owner,'native_owner_class_guid':target.class_guid,
                    'native_owner_record_offset':target.start,'stored_owner_field_offset':owner_offset,
                    'naming_keys':keys,'stored_key_field_offsets':offsets})
            reverse_count_offset=record.body+cursor
            n=number('<I')
            reverse_only = count==0 and n>0
            if (n>1000000 or not reverse_only and n!=len(owned_keys))or cursor+16*n+15!=len(body):
                raise ValueError('Native naming reverse count or exact footer extent disagrees')
            reverse,seen=[],set()
            for _ in range(n):
                position=record.body+cursor
                key,owner=number('<Q'),number('<Q')
                if reverse_only:
                    target=primary.get(owner)
                    if not 1<=key<=0x7fffffff or key in seen or target is None or owner==record.object_id:
                        raise ValueError('Native reverse-only naming key/typed owner is invalid, missing or duplicated')
                elif key in seen or owned_keys.get(key)!=owner:
                    raise ValueError('Native naming forward/reverse owner association is not reciprocal')
                seen.add(key)
                reverse.append({'naming_key':key,'native_owner_object_id':owner,
                    'native_owner_class_guid':primary[owner].class_guid,
                    'stored_key_field_offset':position,'stored_owner_field_offset':position+8})
            if body[cursor:cursor+4]!=bytes(4):
                raise ValueError('Native naming registry footer marker unsupported')
            container_id=reference(body,cursor+4)
            container=primary.get(container_id)
            if container is None or container.class_guid!=OWNER:
                raise ValueError('Native naming registry typed container reference unresolved')
            container_body=data[container.body:container.end]
            if len(container_body)<33 or reference(container_body,len(container_body)-33)!=record.object_id:
                raise ValueError('Native naming registry/container typed backlink disagrees')
            value={'object_id':record.object_id,'class_guid':REGISTRY,'record_offset':record.start,
                'owner_to_keys':forward,'key_to_owner':reverse,'registry_is_empty':not (forward or reverse),'stored_reverse_count_offset':reverse_count_offset,
                'registry_container_object_id':container_id,'registry_container_class_guid':OWNER,
                'container_reference_offset':record.body+cursor+4,'container_backlink_offset':container.end-33,
                'stored_footer_hex':body[cursor:].hex(),'payload_offset':record.body,'payload_byte_count':len(body),
                'payload_hex':body.hex(),'naming_key_namespace':'Opaque positive registry keys, independently distinct from typed native owner object IDs',
                'scope':SCOPE}
            if reverse_only:
                value.update(table_layout='StoredReverseOnly',reciprocity_status='ForwardTableAbsent',scope=REVERSE_ONLY_SCOPE)
                result['scope'] = 'Observed reciprocal or explicitly reverse-only native naming registries; each decoded record retains its own table and identity scope'
            if encode_native_naming_registry(value)!=body:
                raise ValueError('Native naming registry full payload replay disagrees')
            result['decoded'].append(value)
        except (ValueError,KeyError,IndexError,struct.error)as error:
            result['unresolved'].append({'object_id':record.object_id,'reason':str(error)})
    return result
