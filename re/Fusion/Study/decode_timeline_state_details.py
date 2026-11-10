"""Typed shared-state footer extensions and explicit occurrence timeline aliases.

Only bounded footer fields are interpreted. State support is not feature replay,
visibility inference, historical transform replay or a solved assembly state.
Caller features and the existing timeline reader remain unchanged.
"""

import struct

from decode_component_creation import CREATE_COMPONENT, SNAPSHOT, decode_component_creation
from decode_sketch import numbers, reference
from decode_timeline import HISTORY_GUID, feature_state

STATE_SUPPORT = 'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA'
OPTIONAL_SUPPORT = '074F9459-89C2-4B7D-8AB4-DCE67AE944FE'
HELPER = '5FBE538E-139B-46D4-BCAF-CC796D1E1F78'
BOOKKEEPING = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
VARIANT_CLASSES = {
    CREATE_COMPONENT, SNAPSHOT,
    'D57B1A22-9D5A-4D7D-A909-E08C579612CA',  # CopyPaste
    '49004167-470D-4892-B50E-5C589B1486D2',  # BoundaryFill
    '4A782808-FBDD-4351-A10A-F7AE5693D330',  # RemoveBody
    '2A94257F-2020-4B19-9A68-103A2672F1B7',  # Combine
    '8DFDD543-F823-43AA-BDAF-C638E023F0A0',  # Assemble
    'B6678572-C095-4DD1-9348-614677DD0B4A',  # Loft
    '71BBEDD5-81F8-4585-816B-05908C207204',  # MirrorComponent
    '66E375EA-40F1-4115-8D83-0F23DD30593E',  # DerivedInstance
    '1C037A07-4A15-43F6-ABFC-BBF61B9038D4',  # Hole
    '584D9526-EF22-4F6F-9FE1-5FCF1F3CE575',  # Thread
}
SCOPE = 'Observed optional-reference shared feature footers, reciprocal bookkeeping and explicit creation-snapshot occurrence timeline aliases; internal records remain distinct'


def decode_feature_state_footer(data, record, primary_records):
    """Validate one 66/76/86-byte typed footer and return bounded state details.

    ``primary_records`` must contain unique primary identities only. This helper
    also accepts canonical 66-byte footers for independent contrast validation;
    the batch entry point leaves successful existing-reader states untouched.
    """
    body = data[record.body:record.end]
    primary = primary_records
    if primary.get(record.object_id) is not record:
        raise ValueError('Feature footer primary identity is missing or ambiguous')

    def typed(identity, guid):
        target = primary.get(identity)
        if target is None or target.class_guid != guid:
            raise ValueError('Feature state typed support missing, ambiguous or wrong class')
        return data[target.body:target.end]

    results = []
    failures = []
    for length in (66,76,86):
        if len(body) < length:
            continue
        tail = body[-length:]
        try:
            if tail[:5] != bytes(5) or tail[5] not in (0,1) or tail[6] != 0:
                raise ValueError('Unsupported feature state flag prefix')
            support_id = reference(tail,7)
            support = typed(support_id,STATE_SUPPORT)
            if support[:2] != bytes(2):
                raise ValueError('Unobserved feature state support prefix')
            support_count = struct.unpack_from('<I',support,2)[0]
            if support_count > 100000 or len(support) != 14+19*support_count:
                raise ValueError('Unsupported feature state support counted-reference length')
            support_entries = []
            for i in range(support_count):
                identity = reference(support,6+19*i)
                target = primary.get(identity)
                if target is None or target.class_guid not in (
                        'ABA79BE7-D8D2-4C17-B59B-C2035E111F77',
                        '4B31DA1B-FCD6-4527-BC3E-BE1FBAF867FE',
                        '335CC7BD-BBE5-40AA-9E8C-5EC99D427A3A',
                        'C6ACC94D-2248-421C-BFC3-885A5026559F'):
                    raise ValueError('Unobserved feature state support entry class')
                value = struct.unpack_from('<Q',support,17+19*i)[0]
                if value < 1 or (support_entries and value <= support_entries[-1]['stored_u64']):
                    raise ValueError('Unobserved feature state support numeric keys')
                support_entries.append({'object_id':identity,'class_guid':target.class_guid,'stored_u64':value})
            support_counter = struct.unpack_from('<Q',support,6+19*support_count)[0]
            if support_counter != (support_entries[-1]['stored_u64']+1 if support_entries else 1):
                raise ValueError('Unobserved feature state support counter')
            cursor = 18
            optional_id = None
            if tail[cursor] == 0:
                cursor += 1
            else:
                optional_id = reference(tail,cursor)
                if typed(optional_id,OPTIONAL_SUPPORT) != bytes.fromhex('0000010100000000000000000000000000'):
                    raise ValueError('Unobserved optional feature state support payload')
                cursor += 11
            stored_index = struct.unpack_from('<i',tail,cursor)[0]
            if stored_index not in (-1,2,3,4,9):
                raise ValueError('Unobserved feature footer stored integer')
            cursor += 4
            if tail[cursor:cursor+4] != b'\1\1\0\0' or tail[cursor+12:cursor+16] != b'\1\1\0\0':
                raise ValueError('Unsupported feature state scalar markers')
            scalar = numbers(tail,cursor+4,1)[0]
            scalar_start = cursor
            cursor += 16
            helper_id = reference(tail,cursor)
            if typed(helper_id,HELPER) != bytes.fromhex('0001000000000000000000000000'):
                raise ValueError('Unobserved feature footer helper payload')
            cursor += 11
            if tail[cursor] != 1 or tail[cursor+1] != tail[5] or tail[cursor+2] not in (0,1):
                raise ValueError('Feature state repeated suppression/rollback flags disagree')
            rolled_back = bool(tail[cursor+2])
            cursor += 3
            bookkeeping_id = reference(tail,cursor)
            bookkeeping = typed(bookkeeping_id,BOOKKEEPING)
            if (bookkeeping[:6] != bytes(6) or bookkeeping[6] not in (0,1) or bookkeeping[7] not in (0,1)
                    or bookkeeping[-8:] != bytes(8)):
                raise ValueError('Unsupported feature footer bookkeeping prefix/trailer')
            count = struct.unpack_from('<I',bookkeeping,8)[0]
            if count > 100000 or len(bookkeeping) != 39+19*count:
                raise ValueError('Unsupported feature footer bookkeeping counted-reference length')
            entries = []
            for i in range(count):
                identity = reference(bookkeeping,12+19*i)
                if identity not in primary:
                    raise ValueError('Feature footer bookkeeping entry missing or ambiguous')
                entries.append({'object_id':identity,'stored_u64':struct.unpack_from('<Q',bookkeeping,23+19*i)[0]})
            owner_offset = 12+19*count
            if reference(bookkeeping,owner_offset) != record.object_id:
                raise ValueError('Feature footer bookkeeping owner backlink disagrees')
            cursor += 11
            related = None
            if tail[cursor] == 0:
                cursor += 1
            else:
                related = reference(tail,cursor)
                target = primary.get(related)
                if target is None or target.class_guid not in VARIANT_CLASSES:
                    raise ValueError('Unobserved feature footer final related-feature class')
                cursor += 11
            if cursor != len(tail)-1 or tail[cursor] != 0:
                raise ValueError('Unsupported feature state footer suffix')
            # Remove optional references only to reuse already contrasted flags.
            normalized = (tail[:18]+b'\0'+tail[scalar_start-4:scalar_start+16]
                          +tail[scalar_start+16:scalar_start+16+25]+b'\0\0')
            state = feature_state(normalized)
            if state['is_rolled_back'] != rolled_back:
                raise ValueError('Normalized and native rollback flag disagree')
            state['source'] = 'Typed variable-reference shared feature footer; suppression copies agree; native bookkeeping owner backlink validated'
            related_detail = None
            if related is not None:
                target = primary[related]
                related_detail = {'object_id':related,'class_guid':target.class_guid,
                                  'relation':'SelfSnapshot' if related == record.object_id and target.class_guid == SNAPSHOT else
                                             'SnapshotReference' if target.class_guid == SNAPSHOT else 'RelatedFeatureReference',
                                  'scope':'Explicit reference; not TimelineGroup membership or solved-state ownership'}
            results.append({'object_id':record.object_id,'class_guid':record.class_guid,
                'state':state,'footer_offset':record.end-length,'footer_length':length,
                'state_support_object_id':support_id,'support_reference_entries':support_entries,
                'stored_support_counter':support_counter,'optional_support_object_id':optional_id,
                'helper_object_id':helper_id,'bookkeeping_object_id':bookkeeping_id,
                'bookkeeping_reference_entries':entries,
                'stored_bookkeeping_owner_u64':struct.unpack_from('<Q',bookkeeping,owner_offset+11)[0],
                'stored_integer':stored_index,'uninterpreted_finite_scalar':scalar,
                'related_feature_reference':related_detail,
                'raw_state_flags':{'suppression_first':tail[5],'suppression_repeated':int(state['is_suppressed']),
                                   'rollback':int(rolled_back)},
                'scope':'Only flags and explicit typed support/backlink framing; remaining feature schema and support/scalar semantics unresolved'})
        except (ValueError,IndexError,struct.error) as error:
            failures.append(str(error))
    if len(results) != 1:
        raise ValueError('No unique validated feature state footer: '+ '; '.join(failures))
    return results[0]


def decode_timeline_state_details(data, records, features, *, assembly=None, component_creation=None):
    """Return states/occurrence_aliases/unresolved, without mutating features.

    States contain only old-reader failures successfully decoded by this helper.
    Occurrence aliases require independently validated component creation links.
    Pass an existing assembly/creation summary to avoid repeating those readers.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id,[]).append(record)
    primary = {identity:items[0] for identity,items in grouped.items() if len(items)==1}
    states,unresolved,aliases = [],[],[]
    for feature in features:
        record = primary.get(feature['object_id'])
        if record is None or record.class_guid not in VARIANT_CLASSES:
            continue
        try:
            feature_state(data[record.body:record.end])
            continue
        except (ValueError,IndexError,struct.error):
            pass
        try:
            if record.start != feature['record_offset']:
                raise ValueError('Feature state record offset disagrees with caller feature')
            states.append(decode_feature_state_footer(data,record,primary))
        except (ValueError,KeyError,IndexError,struct.error) as error:
            unresolved.append({'object_id':feature['object_id'],'reason':str(error)})
    if assembly is not None:
        creations = (component_creation if component_creation is not None else
                     decode_component_creation(data,records,features,assembly))['decoded']
        occurrences = {o['object_id']:o for o in assembly['native_occurrences']}
        history_members = {}
        for r in primary.values():
            if r.class_guid != HISTORY_GUID:
                continue
            b = data[r.body:r.end]
            try:
                if b[:2] != bytes(2):
                    raise ValueError('Unsupported occurrence-alias history prefix')
                owner = reference(b,2);count = struct.unpack_from('<I',b,13)[0]
                if count>100000 or len(b) != 17+11*count:
                    raise ValueError('Unsupported occurrence-alias history length')
                identities = [reference(b,17+11*i) for i in range(count)]
                if len(set(identities)) != count:
                    raise ValueError('Duplicate occurrence-alias history entries')
                history_members[r.object_id] = (owner,identities)
            except (ValueError,IndexError,struct.error) as error:
                unresolved.append({'object_id':r.object_id,'reason':str(error)})
        state_ids = {s['object_id'] for s in states}
        for c in creations:
            snapshot,creation = c['snapshot_object_id'],c['feature_object_id']
            try:
                if snapshot not in state_ids or creation not in state_ids:
                    raise ValueError('Creation/snapshot bounded state footer unresolved')
                occurrence = occurrences[c['native_occurrence_object_id']]
                for history_id,(owner,identities) in history_members.items():
                    if snapshot not in identities:
                        continue
                    if creation in identities:
                        raise ValueError('Creation and snapshot both occur in the same history list')
                    aliases.append({'history_record_object_id':history_id,'history_owner_object_id':owner,
                        'native_history_entry_object_id':snapshot,'native_history_ordinal':identities.index(snapshot),
                        'creation_feature_object_id':creation,'snapshot_object_id':snapshot,
                        'native_occurrence_object_id':occurrence['object_id'],'entity_kind':'Occurrence',
                        'entity_name':occurrence['explicit_name'] or (c['component_name']+':'+str(occurrence['instance_number']) if c['component_name'] else None),
                        'entity_name_source':'Explicit occurrence name or decoded component name and native instance number',
                        'component_object_id':c['component_object_id'],
                        'component_name':c['component_name'],'occurrence_paths':c['occurrence_paths'],
                        'scope':'Snapshot is the ordered history entry for this explicitly linked occurrence creation; creation feature is absent from this history. No internal snapshot visibility or solved transform inferred.'})
            except (ValueError,KeyError) as error:
                unresolved.append({'object_id':snapshot,'reason':str(error)})
    return {'states':states,'occurrence_aliases':aliases,'unresolved':unresolved,'scope':SCOPE,
            'limitations':'No global snapshot filtering, no guessed feature names/group membership, no unknown integer/scalar semantics, no active timeline replay or solved assembly state'}
