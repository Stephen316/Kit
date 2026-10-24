"""FACE tracking literals corroborated only after independent native BODY joins.

An owned feature descriptor/leaf, historical anchor, reciprocal support, native
body handle mapping and typed ASM BODY/face graph establish context first. The
FPM integer remains a literal; equality with a descriptor ID is secondary
corroboration, not a serialized native reference or selected-face identity.
"""
import struct
import uuid

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_brep import decode_topology
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import attributes,reference
from decode_special_fillets import decode_special_fillets

DESCRIPTOR='5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
FULL='A9D2884D-E7D1-4E8F-8961-B7D90BAC64F1'
SCOPE='Independent owned descriptor/source-feature/anchor/native BODY and same-asset initial ASM face context; literal FPM corroboration only, selected/persistent FACE identity and historical state unqualified'


def decode_face_tracking_contexts(data,records,features,member,members,body_identifier_summary,body_selections=None):
    """Return decoded/unresolved/scope; never clear prior selection warnings."""
    out=dict(decoded=[],unresolved=[],scope=SCOPE)
    if member not in members or members[member]!=data or not member.endswith('/FusionDesignSegmentType1/BulkStream.dat'):
        out['unresolved'].append(dict(reason='FACE tracking Design member/bytes do not establish same-asset scope'))
        return out
    grouped={}
    for r in records:
        if r.is_primary:grouped.setdefault(r.object_id,[]).append(r)
    primary={i:rs[0] for i,rs in grouped.items() if len(rs)==1}
    bodies=decode_body_selections(data,records)
    if body_selections is not None and bodies!=body_selections:
        # Existing callers can add separately decoded body-context metadata.
        for anchor in bodies['body_anchors']:
            supplied=[a for a in body_selections['body_anchors'] if a['object_id']==anchor['object_id']]
            if len(supplied)!=1 or any(supplied[0][k]!=anchor[k] for k in ('native_body_object_id','source_owner_object_id')):
                raise ValueError('FACE tracking supplied body anchor identity disagrees')
    anchors={a['object_id']:a for a in bodies['body_anchors']}
    named={f['object_id']:f for f in features}
    def typed(identity,guid):
        r=primary.get(identity)
        if r is None or r.class_guid!=guid:raise ValueError('FACE tracking typed native reference missing/ambiguous/wrong class')
        return r,data[r.body:r.end]
    # Revalidate the stored native mapping and its exact same-asset filename;
    # no numeric FPM value participates in choosing a BODY or blob.
    mappings=decode_body_asm_identifiers(data,records,member,members,body_identifier_summary)
    cache={}
    def body_context(identity):
        choices=[(m,b) for m in mappings['decoded'] for b in m['bindings'] if b['native_body_object_id']==identity]
        if len(choices)!=1:raise ValueError('FACE tracking body lacks one explicit same-asset mapping')
        m,b=choices[0]
        supplied=[x for mm in body_identifier_summary['decoded'] if mm['mapping_record_object_id']==m['mapping_record_object_id']
                  for x in mm['bindings'] if x['native_body_object_id']==identity]
        if len(supplied)!=1 or any(supplied[0][k]!=b[k] for k in ('stored_handle','asm_body_index')):
            raise ValueError('FACE tracking supplied body/handle association disagrees')
        _,native=typed(identity,'D3937028-C20C-4E65-B010-94AD418A5C20')
        if reference(native,len(native)-11)!=m['owner_object_id']:raise ValueError('FACE tracking native BODY collection ownership disagrees')
        blob_member=m['history_blob_member']
        if blob_member not in cache:
            blob=members[blob_member];parsed=inspect_asm(blob)
            tags=decode_asm_generic_tags(blob,parsed,allow_fpm_tracking=True)
            if tags['unresolved']:raise ValueError('FACE tracking requires complete initial custom-attribute coverage')
            topology=decode_topology(parsed)
            cache[blob_member]=(parsed,tags,topology)
        parsed,tags,topology=cache[blob_member]
        graphs=[g for g in topology['body_graphs'] if g['body_index']==b['asm_body_index']]
        if len(graphs)!=1:raise ValueError('FACE tracking mapped BODY graph absent/ambiguous')
        return m,b,parsed,tags,topology,graphs[0]
    def descriptor_context(identity,owner,guid,source_id,expected_anchor=None):
        _,payload=typed(identity,guid)
        count=0 if guid==DESCRIPTOR else 3
        if (len(payload)!=263+11*count or payload[:2]!=bytes(2) or struct.unpack_from('<I',payload,13)[0]!=1
                or reference(payload,len(payload)-11)!=owner):raise ValueError('FACE tracking owned descriptor framing disagrees')
        namespace,pos=read_string(payload,17);entity,pos=read_string(payload,pos)
        if len(namespace)!=36 or len(entity)!=36 or pos!=169:raise ValueError('FACE tracking descriptor UUID framing disagrees')
        uuid.UUID(namespace);uuid.UUID(entity)
        if payload[169:181]!=struct.pack('<QI',2,count) or struct.unpack_from('<I',payload,181+11*count)[0]!=1:
            raise ValueError('FACE tracking descriptor context/anchor counts disagree')
        anchor_id=reference(payload,185+11*count)
        if expected_anchor is not None and anchor_id!=expected_anchor:raise ValueError('FullRound face tracking anchor copy differs')
        anchor=anchors.get(anchor_id)
        if anchor is None:raise ValueError('FACE tracking explicit historical body anchor unavailable')
        _,raw_anchor=typed(anchor_id,'D26351F0-5940-4D23-AA20-2C35475A6D9E')
        if (len(raw_anchor)!=102 or reference(raw_anchor,80)!=anchor['native_body_object_id']
                or reference(raw_anchor,91)!=source_id or anchor['source_owner_object_id']!=source_id):
            raise ValueError('FACE tracking anchor/source-feature explicit copies disagree')
        support_id=reference(payload,len(payload)-23);_,support=typed(support_id,'6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
        if (len(support)!=77 or support[:12]!=bytes.fromhex('000000000000010102000000')
                or reference(support,12)!=source_id or reference(support,31)!=identity or reference(support,50)!=identity):
            raise ValueError('FACE tracking reciprocal support/source-owner copies disagree')
        return dict(descriptor_object_id=identity,descriptor_class_guid=guid,descriptor_owner_feature_object_id=owner,
            source_feature_object_id=source_id,source_feature_name=named.get(source_id,{}).get('name'),
            body_anchor_object_id=anchor_id,native_body_object_id=anchor['native_body_object_id'],support_record_object_id=support_id,
            namespace_text=namespace,entity_guid_text=entity,
            context_status='Explicit body context only; no individual FACE or source-role mapping')
    candidates=[]
    specials=decode_special_fillets(data,records,features,bodies)
    full_by={x['feature_object_id']:x for x in specials['decoded'] if x['mode']=='FullRound'}
    for feature in features:
        settings=feature.get('tool_settings',{});owner=feature['object_id']
        if feature['kind']=='Fillet' and owner in full_by:
            try:
                provenance=full_by[owner]['historical_body']
                item=descriptor_context(provenance['descriptor_object_id'],owner,FULL,provenance['historical_body_source_owner_object_id'],provenance['body_anchor_object_id'])
                item.update(input_role='FullRoundAggregateBodyContext',input_ordinal=None,
                    face_role_status='FullRound aggregate selects three source face roles; the two stored FPM faces are not assigned to those roles')
                candidates.append(item)
            except (ValueError,KeyError,IndexError,struct.error) as e:out['unresolved'].append(dict(feature_object_id=owner,reason=str(e)))
            continue
        selected=settings.get('input_descriptors',settings.get('input_features',[]))
        if (feature['kind'] not in ('CircularPattern','RectangularPattern','Mirror')
                or settings.get('pattern_entity_type')!='Features' or not selected):continue
        try:
            collection_id=settings['input_entity_collection_object_id']
            _,collection=typed(collection_id,'8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
            count=struct.unpack_from('<I',collection,6)[0]
            if (count not in (1,2) or count!=len(selected) or collection[:6]!=bytes(6) or len(collection)!=74+26*count
                    or reference(collection,10+26*count)!=owner or reference(collection,len(collection)-11)!=owner):
                raise ValueError('FACE tracking source collection counts/owners disagree')
            descriptor_ids=[reference(collection,10+26*i) for i in range(count)]
            if descriptor_ids!=[s['descriptor_object_id'] for s in selected]:raise ValueError('FACE tracking native ordered descriptor input copies disagree')
            proxy_ids=settings.get('input_selection_record_object_ids',[settings.get('input_selection_record_object_id')])
            if len(proxy_ids)!=1:raise ValueError('FACE tracking requires one owned input proxy')
            proxy_record,proxy=typed(proxy_ids[0],'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
            refs,props=native_proxy_references(data,proxy_record)
            if props or refs!=descriptor_ids or reference(proxy,len(proxy)-11)!=owner:raise ValueError('FACE tracking collection/proxy/owner copies disagree')
            native_feature=primary.get(owner)
            if native_feature is None or native_feature.class_guid!=feature['class_guid']:raise ValueError('FACE tracking native feature class disagrees')
            raw_feature=data[native_feature.body:native_feature.end]
            if feature['kind']=='CircularPattern':collection_position=17
            else:collection_position=(attributes(raw_feature,2)[1] if raw_feature[1] else 2)+11
            if reference(raw_feature,collection_position)!=collection_id:raise ValueError('FACE tracking feature does not explicitly own selected collection')
            for ordinal,selected_input in enumerate(selected):
                identity=descriptor_ids[ordinal];_,descriptor=typed(identity,DESCRIPTOR)
                leaf_id=reference(descriptor,2);_,leaf=typed(leaf_id,'90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
                if len(leaf)!=10 or leaf[:2]!=bytes(2):raise ValueError('FACE tracking source-feature leaf framing disagrees')
                source_id=struct.unpack_from('<Q',leaf,2)[0];typed(source_id,'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
                if source_id==owner or source_id!=selected_input['source_feature_object_id']:raise ValueError('FACE tracking source feature leaf/cached input disagrees')
                item=descriptor_context(identity,owner,DESCRIPTOR,source_id)
                item.update(input_role='ExplicitExtrudeFeatureInput',input_ordinal=ordinal,
                    input_entity_collection_object_id=collection_id,input_selection_proxy_object_id=proxy_ids[0],terminal_feature_leaf_object_id=leaf_id)
                candidates.append(item)
        except (ValueError,KeyError,IndexError,struct.error) as e:out['unresolved'].append(dict(feature_object_id=owner,reason=str(e)))
    for context in candidates:
        try:
            m,b,parsed,tags,topology,graph=body_context(context['native_body_object_id'])
            # Membership is established independently of every FPM number.
            face_rows=[r for r in tags['ignored_validated_other_definition_attributes']
                if r['definition_name']=='FPM_tracked_attrib_def' and r['owner_kind']=='face'
                and r['owner_record_index'] in graph['face_indices']]
            if not face_rows:continue
            matched=[r for r in face_rows if r['stored_tracking_literal']==context['descriptor_object_id']]
            if len(matched)!=len(face_rows):raise ValueError('Independent descriptor/BODY context has noncorroborating FACE FPM literals')
            out['decoded'].append(dict(feature_object_id=context['descriptor_owner_feature_object_id'],native_context=context,
                mapping_record_object_id=m['mapping_record_object_id'],history_blob_member=m['history_blob_member'],
                stored_native_BODY_handle=b['stored_handle'],initial_ASM_BODY_record_index=b['asm_body_index'],
                mapped_BODY_FACE_record_indices=graph['face_indices'],corroborating_FACE_tracking_attributes=matched,
                tracked_FACE_count=len(matched),tracking_covers_all_mapped_BODY_faces=len(matched)==len(graph['face_indices']),
                descriptor_ID_equals_stored_literal=True,literal_is_serialized_native_reference=False,
                exact_selected_source_FACE_identity=None,persistent_FACE_identity=None,qualified_historical_state=None,scope=SCOPE))
        except (ValueError,KeyError,IndexError,struct.error) as e:out['unresolved'].append(dict(descriptor_object_id=context['descriptor_object_id'],reason=str(e)))
    return out
