"""Observed additional Mirror/Scale inputs and typed component/datum provenance.

Unusual MirrorComponent/datum class GUIDs below are copied from primary metadata
in actual exported archives, not inferred from labels. Component/datum paths
remain separate provenance summaries without regeneration/lifecycle claims.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import uuid

from decode_assembly import OCCURRENCE_GUID, occurrence as read_occurrence
from decode_body_tools import decode_body_tool
from decode_face_selections import resolve_native_faces
from decode_mirror_modes import MIRROR, decode_mirror_modes
from decode_parameters import read_string
from decode_placement import rigid_matrix
from decode_scale_inputs import SCALE, decode_scale_sketch
from decode_selection import known_construction_entities, native_proxy_references, resolve_native_selection
from decode_sketch import attributes, numbers, reference, same

MIRROR_COMPONENT = '71BBEDD5-81F8-4585-816B-05908C207204'
MIRROR_DATUM = 'A7B2C3D4-9E8F-4A5B-8C1D-6E7F0A1B2C3D'


def _access(data, records):
    grouped = {}
    for r in records:
        if r.is_primary:
            grouped.setdefault(r.object_id, []).append(r)
    primary = {i: items[0] for i, items in grouped.items() if len(items) == 1}
    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Additional input typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]
    return primary, typed


def _proxy(data, typed, identity, owner):
    record, payload = typed(identity, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    ids, props = native_proxy_references(data, record)
    if props or reference(payload, len(payload)-11) != owner:
        raise ValueError('Additional input proxy attributes/owner mismatch')
    return ids


def _known_descriptor(typed, identity, owner, known, size):
    _, body = typed(identity, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
    if (len(body) != size or body[:2] != bytes(2) or struct.unpack_from('<I', body, 13)[0] != 1
            or reference(body, size-11) != owner):
        raise ValueError('Additional datum descriptor count/owner mismatch')
    leaf_id = reference(body, 2)
    _, leaf = typed(leaf_id, '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
    if len(leaf) != 10 or leaf[:2] != bytes(2):
        raise ValueError('Additional datum leaf framing unsupported')
    source_id = struct.unpack_from('<Q', leaf, 2)[0]
    if source_id not in known or known[source_id]['kind'] != 'ConstructionPlane':
        raise ValueError('Explicit native construction-plane ID unresolved')
    return {'descriptor_object_id': identity, 'terminal_object_id': leaf_id, 'entity': known[source_id],
            'association': 'Owned typed descriptor/leaf explicitly selects known native construction-plane ID'}


def decode_mirror_face_inputs(data, records, body, feature, known):
    result = decode_body_tool(data, records, body, feature, known)
    _, typed = _access(data, records)
    props, cursor = attributes(body, 2) if body[1] else ({},2)
    if props or feature['class_guid'] != MIRROR:
        raise ValueError('Unsupported additional face-Mirror feature')
    _, control = typed(reference(body, cursor), 'C444E6AD-33DC-4877-B037-A3A5518856B1')
    if (len(control) != 133 or reference(control, 107) != feature['object_id']
            or struct.unpack_from('<II', control, 37) != (2,0)):
        raise ValueError('Only captured face-input/inactive-compute Mirror control supported')
    collection_id = reference(body,cursor+11)
    _, collection = typed(collection_id, '8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
    if (len(collection) != 137 or collection[:6] != bytes(2)+struct.pack('<I',1)
            or struct.unpack_from('<I',collection,17)[0] != 2
            or reference(collection,73) != feature['object_id']
            or reference(collection,126) != feature['object_id']):
        raise ValueError('Unobserved face-Mirror counted contexts/inputs/owner')
    context_id = reference(collection,6)
    typed(context_id,'C46D3EEB-40E1-43FA-83DC-9CB204335417')
    descriptor_ids=[]
    associations=[]
    for position in (21,47):
        if struct.unpack_from('<I',collection,position+11)[0] != 1:
            raise ValueError('Unobserved face-Mirror per-input association count')
        identity=reference(collection,position)
        association_id=reference(collection,position+15)
        typed(association_id,'C46D3EEB-40E1-43FA-83DC-9CB204335417')
        descriptor_ids.append(identity)
        associations.append(association_id)
    proxy_id=reference(control,118)
    if _proxy(data,typed,proxy_id,feature['object_id']) != descriptor_ids:
        raise ValueError('Face-Mirror collection/proxy ordered descriptors disagree')
    faces=resolve_native_faces(data,records,proxy_id,feature['object_id'])
    if faces['attributes'] or len(faces['faces']) != 2 or [f['descriptor_object_id'] for f in faces['faces']] != descriptor_ids:
        raise ValueError('Face-Mirror bounded source recipes unresolved')
    plane_ids=_proxy(data,typed,result['plane_selection_record_object_id'],feature['object_id'])
    if len(plane_ids)!=1 or result['plane'] is None:
        raise ValueError('Only captured explicit ConstructionPlane for face-Mirror supported')
    _known_descriptor(typed,plane_ids[0],feature['object_id'],known,263)
    if not math.isfinite(result['stitch_tolerance_cm']):
        raise ValueError('Nonfinite Mirror tolerance')
    selected=[{'kind':'Face',**face,'association_record_object_id':association} for face,association in zip(faces['faces'],associations)]
    result.update(input_kind='Face',input_count=2,input_body_count=0,input_face_count=2,input_feature_count=0,
                  input_selections=selected,input_entity_collection_object_id=collection_id,
                  input_selection_record_object_ids=[proxy_id],input_collection_context_object_ids=[context_id],
                  pattern_entity_type='Faces',pattern_entity_type_code=0,pattern_compute_option_code=2,
                  pattern_compute_option=None,compute_applies_to_feature_inputs=False,
                  input_selection_status='Explicit ordered owned face recipes and historical body anchors; exact ASM face IDs and mirrored result geometry unresolved')
    return result


def inspect_mirror_datum_input(data,records,body,feature,known):
    _,typed=_access(data,records)
    owner=feature['object_id']
    if feature['class_guid']!=MIRROR_DATUM or len(body)!=296 or body[:3]!=bytes(3):
        raise ValueError('Unobserved metadata-typed datum-Mirror feature layout')
    control_id=reference(body,3)
    _,control=typed(control_id,'C444E6AD-33DC-4877-B037-A3A5518856B1')
    if (len(control)!=107 or control[:4]!=bytes(4) or control[15:27]!=bytes(12)
            or struct.unpack_from('<II',control,27)!=(2,4) or reference(control,81)!=owner):
        raise ValueError('Unobserved datum-Mirror control/raw-mode/owner layout')
    source_proxy=reference(control,92)
    source_ids=_proxy(data,typed,source_proxy,owner)
    if len(source_ids)!=1:
        raise ValueError('Only captured single construction-plane input supported')
    source=_known_descriptor(typed,source_ids[0],owner,known,252)
    typed(source['entity']['object_id'],'8D424E29-DE23-4B1F-A3AD-84C52A497D1A')
    source_association=reference(control,48)
    _,association=typed(source_association,'E8F5A2B1-4C3D-4E7F-9A8B-1D2E3F4A5B6C')
    if (len(association)!=40 or association[:10]!=bytes(10)
            or struct.unpack_from('<I',association,10)[0]!=1
            or reference(association,14)!=source['entity']['object_id']
            or struct.unpack_from('<I',association,25)[0]!=1 or reference(association,29)!=control_id):
        raise ValueError('Datum-Mirror source association/control ownership disagrees')
    plane_proxy=reference(control,4)
    plane_ids=_proxy(data,typed,plane_proxy,owner)
    if len(plane_ids)!=1:
        raise ValueError('Datum-Mirror plane source count unsupported')
    plane=_known_descriptor(typed,plane_ids[0],owner,known,263)
    return {'feature_object_id':owner,'feature_class_guid':MIRROR_DATUM,'native_kind_label':'Mirror',
            'status':'ObservedDatumMirrorSourceProvenance','control_record_object_id':control_id,
            'input_kind':'ConstructionPlane','input_count':1,'input_selections':[source],
            'input_selection_record_object_id':source_proxy,'input_association_object_id':source_association,
            'mirror_plane':plane,'mirror_plane_selection_object_id':plane_proxy,
            'stored_api_compute_corresponding_code':2,'compute_applies_to_feature_inputs':False,
            'stored_input_kind_code':4,'is_combine':None,'stitch_tolerance_cm':None,
            'controls_status':'No stitch binding in this observed control layout; general combine/tolerance semantics and API getter availability remain unresolved',
            'scope':'Exact owned source/plane identities and cached source geometry only; reflected datum creation, result ownership/lifecycle and general operation semantics not reconstructed',
            'identifier_scope':'Full class GUIDs read from actual primary metadata records, including unusual datum/control-association identifiers'}


def inspect_mirror_occurrence_input(data,records,body,feature,known,assembly):
    _,typed=_access(data,records)
    owner=feature['object_id']
    if (feature['class_guid']!=MIRROR_COMPONENT or len(body)!=542 or body[:2]!=bytes(2)
            or body[13:20]!=bytes.fromhex('00000101000000') or body[31:35]!=bytes(4)
            or struct.unpack_from('<I',body,60)[0]!=1):
        raise ValueError('Unobserved metadata-typed component-Mirror feature layout/count')
    source_id=reference(body,64)
    source_record,_=typed(source_id,OCCURRENCE_GUID)
    source=read_occurrence(data[source_record.payload_start:source_record.end],source_id)
    component_id=reference(body,186)
    if source['component_object_id']!=component_id:
        raise ValueError('MirrorComponent explicit source occurrence/component copies disagree')
    typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    components={c['object_id']:c for c in assembly['components']}
    if component_id not in components:
        raise ValueError('MirrorComponent source component name unresolved')
    frame_id=reference(body,171)
    _,frame=typed(frame_id,'2E3AC990-483D-4A55-8662-C064B976A957')
    if (len(frame)!=196 or frame[:20]!=bytes(20) or struct.unpack_from('<I',frame,20)[0]!=3
            or frame[24:39]!=bytes(15) or frame[167]!=0 or reference(frame,168)!=owner or frame[190:]!=bytes(6)):
        raise ValueError('MirrorComponent selected-source frame layout/owner unsupported')
    cache=rigid_matrix(numbers(frame,39,16))
    wrapper_id=reference(frame,179)
    _,wrapper=typed(wrapper_id,'FF415D89-A1DB-44AC-B824-E9A772B86ED4')
    if len(wrapper)!=18 or wrapper[:7]!=bytes.fromhex('00000001000000'):
        raise ValueError('MirrorComponent source route wrapper count unsupported')
    route_id=reference(wrapper,7)
    _,route=typed(route_id,'96CBEA21-17E0-4BCB-BA77-04EA87B47934')
    if len(route)!=406 or route[:6]!=bytes.fromhex('000001000000'):
        raise ValueError('MirrorComponent single source route unsupported')
    instance,cursor=read_string(route,6)
    namespace,cursor=read_string(route,cursor)
    entity,cursor=read_string(route,cursor)
    for text in (instance,namespace,entity):uuid.UUID(text)
    if instance!=source['instance_guid_text'] or route[cursor:cursor+8]!=struct.pack('<Q',2):
        raise ValueError('MirrorComponent route does not select explicit source occurrence')
    namespace_two,cursor=read_string(route,cursor+8)
    endpoint,cursor=read_string(route,cursor)
    uuid.UUID(endpoint)
    if namespace_two!=namespace or route[cursor:]!=struct.pack('<QI',2,0):
        raise ValueError('MirrorComponent source route namespace/footer mismatch')
    derived_id=reference(body,20)
    _,derived=typed(derived_id,'66E375EA-40F1-4115-8D83-0F23DD30593E')
    if len(derived)!=563 or derived[:2]!=bytes(2) or reference(derived,2)!=owner:
        raise ValueError('MirrorComponent derived-instance reciprocal owner mismatch')
    instance_link_id=reference(derived,17)
    _,instance_link=typed(instance_link_id,'2D6E13A1-BBEF-4FB3-9277-00D99F634136')
    if len(instance_link)!=39 or instance_link[:2]!=bytes(2) or reference(instance_link,28)!=derived_id:
        raise ValueError('MirrorComponent derived-occurrence link reciprocal owner mismatch')
    target_id=reference(instance_link,2)
    target_record,_=typed(target_id,OCCURRENCE_GUID)
    target=read_occurrence(data[target_record.payload_start:target_record.end],target_id)
    if target['component_object_id'] not in components:
        raise ValueError('MirrorComponent derived target component unresolved')
    geometry_id=reference(body,2)
    _,geometry=typed(geometry_id,'7B6C3C2D-4096-4E6D-B225-699E8C2D9355')
    descriptor_id=reference(body,315)
    if len(geometry)!=322 or reference(geometry,223)!=descriptor_id or reference(geometry,311)!=owner:
        raise ValueError('MirrorComponent plane descriptor/geometry reciprocal owner mismatch')
    plane=_known_descriptor(typed,descriptor_id,owner,known,263)
    def selected_occurrence(item):
        paths=[p['path'] for p in assembly.get('occurrence_paths',[]) if p['native_occurrence_object_id']==item['object_id']]
        return {'native_occurrence_object_id':item['object_id'],'component_object_id':item['component_object_id'],
                'component_name':components[item['component_object_id']]['name'],'instance_guid_text':item['instance_guid_text'],
                'occurrence_paths':paths,'stored_local_transform':item['local_transform'],
                'placement_scope':'Stored occurrence-cache placement; no feature regeneration or assembly/joint solving applied'}
    return {'feature_object_id':owner,'feature_class_guid':MIRROR_COMPONENT,'native_kind_label':'MirrorComponent',
            'status':'ObservedOccurrenceMirrorSourceAndDerivedProvenance','input_kind':'Occurrence','input_count':1,
            'source_occurrence':selected_occurrence(source),'derived_occurrence':selected_occurrence(target),
            'source_frame_object_id':frame_id,'source_route_wrapper_object_id':wrapper_id,'source_route_object_id':route_id,
            'route_namespace_text':namespace,'route_entity_guid_text':entity,'route_endpoint_guid_text':endpoint,
            'stored_source_context_matrix':cache,'derived_instance_feature_object_id':derived_id,
            'derived_occurrence_link_object_id':instance_link_id,'mirror_plane':plane,
            'is_combine':None,'stitch_tolerance_cm':None,'compute_applies_to_feature_inputs':False,
            'controls_status':'Type-specific combine/tolerance controls remain unresolved; missing API values must not be interpreted as verified null semantics',
            'scope':'Explicit source occurrence ID independently corroborated by owned frame route, and reciprocal derived-instance/occurrence links. General reflection operation, lifecycle and geometry regeneration unresolved.',
            'identifier_scope':'MirrorComponent full GUID and related classes read from actual exported primary metadata, not inferred from labels'}


def decode_remaining_body_input(data,records,body,feature,known,features,assembly):
    guid=feature['class_guid']
    if guid==SCALE:
        return {'status':'DecodedSettings','settings':decode_scale_sketch(data,records,body,feature,known,features,allowed_sketch_counts=(1,2))}
    if guid==MIRROR:
        props,cursor=attributes(body,2) if body[1] else ({},2)
        _,typed=_access(data,records)
        _,control=typed(reference(body,cursor),'C444E6AD-33DC-4877-B037-A3A5518856B1')
        if len(control)!=133:raise ValueError('Unobserved Mirror control length')
        if struct.unpack_from('<I',control,41)[0]==0:
            settings=decode_mirror_face_inputs(data,records,body,feature,known)
        else:
            settings=decode_mirror_modes(data,records,body,feature,known,features,allowed_feature_counts=(1,2))
        return {'status':'DecodedSettings','settings':settings}
    if guid==MIRROR_DATUM:
        return {'status':'PartialProvenance','provenance':inspect_mirror_datum_input(data,records,body,feature,known)}
    if guid==MIRROR_COMPONENT:
        return {'status':'PartialProvenance','provenance':inspect_mirror_occurrence_input(data,records,body,feature,known,assembly)}
    raise ValueError('Unsupported additional Mirror/Scale input class')


def validate_fixtures(root,zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder=root/'remainingbodyinputs-7b3357274e85'
    truth=json.loads((folder/'ground_truth.json').read_text())
    assert len(truth['samples'])==5 and not truth['errors'] and (folder/'complete.txt').is_file()
    report={'api_version':truth['fusion_version'],'samples':[],'negative_checks':[],
            'interface':'decode_remaining_body_input(data,records,body,feature,known,features,assembly) -> status DecodedSettings/settings or PartialProvenance/provenance',
            'integration':'Three settings cases can populate tool_settings. MirrorComponent and datum Mirror remain separate provenance summaries; do not mark them generally decoded or claim reflection regeneration. Feature/Face/Sketch inputs already resolved here should skip generic body-only selection pass.',
            'validation_command':'python3 decode_remaining_body_inputs.py --validate --zstd-library <local libzstd path>'}
    cases={}
    def read_archive(archive):
        main=decode_basics(archive,zstd_library)
        stream=next(s for s in main['streams'] if s.get('features'))
        members=read_members(archive,zstd_library)
        data=members[stream['member']]
        records,_=design_records(data,members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by={r.object_id:r for r in records if r.is_primary}
        known=known_construction_entities(data,records,stream['features'])
        return data,records,stream,by,known
    for sample in truth['samples']:
        expected_errors={'mirror_occurrence':{'isCombine','stitchTolerance'},
                         'mirror_construction_plane':{'mirrorPlane','isCombine','stitchTolerance'}}.get(sample['case'],set())
        assert {e['field'] for e in sample['getter_errors']}==expected_errors
        archive=folder/sample['file']
        data,records,stream,by,known=read_archive(archive)
        feature=next(f for f in stream['features'] if f.get('name')=='ProbeRemainingBodyInput')
        record=by[feature['object_id']]
        body=data[record.body:record.end]
        direct_feature={k:v for k,v in feature.items() if k!='tool_settings'}
        out=decode_remaining_body_input(data,records,body,direct_feature,known,stream['features'],stream['assembly_decoding'])
        decoded=out.get('settings',out.get('provenance'))
        api=sample['settings']
        checks={'actual_feature_class_from_primary_metadata':feature['class_guid']==record.class_guid,
                'input_count_matches_actual':decoded['input_count']==len(sample['actual_inputs'])}
        kind=decoded['input_kind']
        if kind=='Feature':
            checks.update(source_feature_names_and_order_match_actual=[f['source_feature_name'] for f in decoded['input_features']]==[f['name'] for f in sample['actual_inputs']],
                          source_feature_types_match_actual=[f['source_feature_kind']+'Feature' for f in decoded['input_features']]==[f['entity_type'].split('::')[-1] for f in sample['actual_inputs']],
                          active_compute_matches_actual=decoded['pattern_compute_option_code']==api['stored_api_compute_getter'] and decoded['compute_applies_to_feature_inputs'],
                          combine_and_tolerance_match_actual=decoded['is_combine']==api['is_combine'] and same([decoded['stitch_tolerance_cm']],[api['stitch_tolerance_cm']]))
        elif kind=='Face':
            names={b['object_id']:b['name'] for b in stream['body_properties']['bodies']}
            checks.update(face_types_match_actual=all(f['entity_type']=='adsk::fusion::BRepFace' for f in sample['actual_inputs']),
                          ordered_historical_body_names_match_actual=[names[f['native_body_object_id']] for f in decoded['input_selections']]==[f['source_body']['name'] for f in sample['actual_inputs']],
                          ordered_bounded_recipe_sources_retained=all(f['recipe']['payload_kind']=='bounded_face_recipe_data' for f in decoded['input_selections']),
                          body_vs_face_counts_correct=decoded['input_body_count']==0 and decoded['input_face_count']==2,
                          inactive_compute_preserved=decoded['pattern_compute_option_code']==api['stored_api_compute_getter'] and decoded['compute_applies_to_feature_inputs'] is False and decoded['pattern_compute_option'] is None,
                          combine_and_tolerance_match_actual=decoded['is_combine']==api['is_combine'] and same([decoded['stitch_tolerance_cm']],[api['stitch_tolerance_cm']]))
        elif kind=='Sketch':
            checks.update(ordered_sketch_names_match_actual=[s['sketch_name'] for s in decoded['input_selections']]==[s['sketch_name'] for s in sample['actual_inputs']],
                          actual_input_types_are_Sketch=all(s['entity_type']=='adsk::fusion::Sketch' for s in sample['actual_inputs']),
                          factor_and_uniform_match_actual=decoded['is_uniform']==api['is_uniform'] and same([decoded['factor']],[api['factor']]),
                          reference_point_geometry_matches_actual=same(decoded['point']['entity']['position_cm'],sample['actual_point']['position_cm']),
                          root_sketch_ids_are_distinct=len({s['sketch_object_id'] for s in decoded['input_selections']})==2)
        elif kind=='ConstructionPlane':
            source=decoded['input_selections'][0]['entity'];actual=sample['actual_inputs'][0]
            checks.update(actual_source_type_matches=actual['entity_type']=='adsk::fusion::ConstructionPlane',
                          source_name_matches_actual=source['name']==actual['name'],
                          source_cached_origin_normal_match_actual=same(source['origin_cm'],actual['origin_cm']) and same(source['normal'],actual['normal']),
                          unavailable_controls_retained_as_unknown=decoded['is_combine'] is None and decoded['stitch_tolerance_cm'] is None and api['is_combine'] is None and api['stitch_tolerance_cm'] is None and expected_errors=={'mirrorPlane','isCombine','stitchTolerance'},
                          partial_lifecycle_status_preserved=out['status']=='PartialProvenance')
        else:
            actual=sample['actual_inputs'][0]
            source=decoded['source_occurrence'];target=decoded['derived_occurrence']
            actual_targets=[o for o in sample['root_occurrences_after'] if o['component_name']==target['component_name']]
            checks.update(source_type_matches_actual=actual['entity_type']=='adsk::fusion::Occurrence',
                          source_native_path_matches_actual=source['occurrence_paths']==[actual['full_path_name']],
                          source_component_name_matches_actual=source['component_name']==actual['component_name'],
                          source_cached_matrix_matches_actual=same(source['stored_local_transform'],actual['transform']) and same(decoded['stored_source_context_matrix'],actual['transform']),
                          derived_native_path_matches_actual=len(actual_targets)==1 and target['occurrence_paths']==[actual_targets[0]['full_path_name']],
                          derived_cached_matrix_matches_actual=len(actual_targets)==1 and same(target['stored_local_transform'],actual_targets[0]['transform']),
                          unavailable_controls_retained_as_unknown=decoded['is_combine'] is None and decoded['stitch_tolerance_cm'] is None and api['is_combine'] is None and api['stitch_tolerance_cm'] is None and expected_errors=={'isCombine','stitchTolerance'},
                          partial_lifecycle_status_preserved=out['status']=='PartialProvenance')
        if sample['case'].startswith('mirror'):
            selected_plane=decoded.get('plane',decoded.get('mirror_plane'))
            actual_plane=sample['actual_mirror_plane']
            if actual_plane is None:
                actual_plane=sample['requested_mirror_plane']
                plane_check='native_mirror_plane_matches_requested_only_actual_getter_unavailable'
            else:
                plane_check='mirror_plane_source_matches_actual'
            checks[plane_check]=(selected_plane is not None and selected_plane['entity']['kind']=='ConstructionPlane'
                 and selected_plane['entity']['name']==actual_plane['name'] and same(selected_plane['entity']['origin_cm'],actual_plane['origin_cm'])
                 and same(selected_plane['entity']['normal'],actual_plane['normal']))
        assert all(checks.values()),(sample['file'],checks)
        report['samples'].append({'archive':str(archive.relative_to(root)),'checks':checks,'decoded':out,
                                  'actual_inputs':sample['actual_inputs'],'actual_settings':api,
                                  'actual_getter_errors':sample['getter_errors'],
                                  'scope':'Face recipe ordering preserves native source fields, without identifying each recipe as a particular ASM face; occurrence matrices are cache comparisons only'})
        cases[sample['case']]=(data,records,stream,by,known,direct_feature,out)
    mutations=[('mirror_two_features','Second feature descriptor owner mismatch',cases['mirror_two_features'][-1]['settings']['input_features'][1]['descriptor_object_id'],253,struct.pack('<Q',999999)),
               ('mirror_boss_faces','Face input leading context count disagrees with bounded collection',cases['mirror_boss_faces'][-1]['settings']['input_entity_collection_object_id'],2,struct.pack('<I',2)),
               ('mirror_occurrence','Source occurrence identity absent',cases['mirror_occurrence'][-1]['provenance']['feature_object_id'],65,struct.pack('<Q',999999)),
               ('mirror_construction_plane','Source datum association reciprocal control owner mismatch',cases['mirror_construction_plane'][-1]['provenance']['input_association_object_id'],30,struct.pack('<Q',999999)),
               ('scale_two_sketches','Second Sketch source leaf identity absent',cases['scale_two_sketches'][-1]['settings']['input_selections'][1]['terminal_object_id'],2,struct.pack('<Q',999999))]
    for case_name,label,identity,offset,replacement in mutations:
        data,records,stream,by,known,feature,out=cases[case_name]
        record=by[identity];changed=bytearray(data)
        changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        feature_record=by[feature['object_id']]
        try:
            decode_remaining_body_input(bytes(changed),records,bytes(changed[feature_record.body:feature_record.end]),feature,known,stream['features'],stream['assembly_decoding'])
        except (ValueError,KeyError,IndexError,struct.error) as error:
            report['negative_checks'].append({'check':label,'passed':True,'reason':str(error)})
        else:raise AssertionError(label)
    for case_name,reader in (('mirror_two_features',decode_mirror_modes),('scale_two_sketches',decode_scale_sketch)):
        data,records,stream,by,known,feature,out=cases[case_name];record=by[feature['object_id']]
        try:reader(data,records,data[record.body:record.end],feature,known,stream['features'])
        except ValueError as error:report['negative_checks'].append({'check':case_name+' remains rejected by exact default count opt-in','passed':True,'reason':str(error)})
        else:raise AssertionError(case_name+' default unexpectedly widened')
    # Compare old decoder defaults against their saved pre-extension reports.
    old_mirror=json.loads((root/'mirror-mode-decoding.json').read_text())
    old_scale=json.loads((root/'scale-shell-input-decoding.json').read_text())
    default_checks=[]
    for sample in old_mirror['samples']:
        data,records,stream,by,known=read_archive(root/sample['archive'])
        feature=next(f for f in stream['features'] if f['kind']=='Mirror');record=by[feature['object_id']]
        result=decode_mirror_modes(data,records,data[record.body:record.end],feature,known,stream['features'])
        assert result==sample['decoded'],sample['archive']
        default_checks.append({'archive':sample['archive'],'exact_saved_default_output_preserved':True})
    sample=next(s for s in old_scale['samples'] if s['archive'].endswith('scale_sketch.f3d'))
    data,records,stream,by,known=read_archive(root/sample['archive'])
    feature=next(f for f in stream['features'] if f['kind']=='Scale');record=by[feature['object_id']]
    result=decode_scale_sketch(data,records,data[record.body:record.end],feature,known,stream['features'])
    assert result==sample['decoded_settings']
    default_checks.append({'archive':sample['archive'],'exact_saved_default_output_preserved':True})
    report['unchanged_default_outputs']=default_checks
    report['coverage']={'new_captures':5,'full_settings_cases':3,'separate_partial_provenance_cases':2,'malformed_guards':5,'count_opt_in_guards':2,'exact_previous_defaults':5}
    report['limitations']=['New helpers use exact full class GUIDs verified from actual primary metadata, including unusual datum Mirror/association identifiers.',
                           'Occurrence and datum Mirror combine/tolerance getters fail with InternalValidationError; datum mirrorPlane getter also returnsNone. Their null API fields are unavailable evidence, not confirmed null semantics. Datum native YZ selection is corroborated only by the request.',
                           'Two-Extrude and two-Sketch support requires explicit keyword opt-ins; old single-input defaults and saved outputs remain exact.',
                           'Face inputs resolve owned recipes/historical bodies in native order; exact selected ASM face identities and regeneration remain unresolved.',
                           'MirrorComponent source/derived occurrence links are exact, but general reflection/lifecycle and solved placement are not claimed; matrices stay labeled stored caches.',
                           'Construction-plane input identifies source and mirror plane; reflected output datum creation/lifecycle remains unresolved and stays outside full tool settings.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',required=True,action='store_true')
    parser.add_argument('--zstd-library',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('remaining-body-input-decoding.json'))
    args=parser.parse_args()
    report=validate_fixtures(Path(__file__).resolve().parent,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'samples':len(report['samples']),'negative_checks':len(report['negative_checks']),
                      'previous_defaults':len(report['unchanged_default_outputs']),'output':str(args.output)}))
