"""Observed datum-Mirror source/output associations and oriented plane caches.

Native references establish identity/ownership. API collection geometry supplies
independent cache contrasts; actual resultFeatures is null in both fixtures.
No general reflection regeneration or API timeline ownership is inferred.
"""

import argparse
import json
from pathlib import Path
import struct

from decode_parameters import read_string
from decode_placement import cross, rigid_matrix
from decode_remaining_body_inputs import MIRROR_DATUM, _access, _known_descriptor, _proxy
from decode_selection import known_construction_entities
from decode_sketch import attributes, numbers, reference, same


PLANE = '8D424E29-DE23-4B1F-A3AD-84C52A497D1A'
ASSOCIATION = 'E8F5A2B1-4C3D-4E7F-9A8B-1D2E3F4A5B6C'


def decode_mirror_datum_outputs(data,records,body,feature,known):
    primary,typed=_access(data,records)
    owner=feature['object_id']
    if feature['class_guid']!=MIRROR_DATUM or len(body)<296 or body[:3]!=bytes(3):
        raise ValueError('Not a bounded observed metadata-typed datum Mirror')
    control_id=reference(body,3)
    _,control=typed(control_id,'C444E6AD-33DC-4877-B037-A3A5518856B1')
    if (len(control)!=107 or control[:4]!=bytes(4) or control[15:27]!=bytes(12)
            or struct.unpack_from('<II',control,27)!=(2,4) or reference(control,81)!=owner):
        raise ValueError('Unsupported datum-Mirror control modes/owner')
    source_proxy=reference(control,92)
    source_ids=_proxy(data,typed,source_proxy,owner)
    if len(source_ids)!=1:raise ValueError('Only observed one datum Mirror input supported')
    selected=_known_descriptor(typed,source_ids[0],owner,known,252)
    source_id=selected['entity']['object_id']
    source_association_id=reference(control,48)
    _,source_association=typed(source_association_id,ASSOCIATION)
    if (len(source_association)!=40 or source_association[:10]!=bytes(10)
            or struct.unpack_from('<I',source_association,10)[0]!=1
            or reference(source_association,14)!=source_id
            or struct.unpack_from('<I',source_association,25)[0]!=1
            or reference(source_association,29)!=control_id):
        raise ValueError('Datum Mirror source association/control owner mismatch')
    output_association_id=reference(control,59)
    _,association=typed(output_association_id,ASSOCIATION)
    if (len(association)!=49 or association[:6]!=bytes(2)+struct.pack('<I',1)
            or struct.unpack_from('<Q',association,6)[0]!=source_id
            or association[14:23]!=bytes.fromhex('010000000101000000')
            or struct.unpack_from('<I',association,34)[0]!=2
            or reference(association,38)!=control_id):
        raise ValueError('Datum Mirror explicit source/output association/owner mismatch')
    output_id=reference(association,23)
    if output_id==source_id:raise ValueError('Datum Mirror source/output identities coincide')

    def plane_cache(identity,expected_owner,expected_orientation):
        record,chunk=typed(identity,PLANE)
        if chunk[:2]!=b'\0\1':raise ValueError('Unsupported datum plane cache prefix')
        props,cursor=attributes(chunk,2)
        if props!={'EntityGenesis':0} or len(chunk)<cursor+109:
            raise ValueError('Unsupported datum plane cache attributes/bounds')
        if struct.unpack_from('<I',chunk,cursor)[0]!=1 or chunk[cursor+20]!=expected_orientation:
            raise ValueError('Unsupported datum plane cached mode/orientation flag')
        origin_and_axes=numbers(chunk,cursor+21,9)
        origin,x_axis,y_axis=origin_and_axes[:3],origin_and_axes[3:6],origin_and_axes[6:]
        natural_normal=cross(x_axis,y_axis)
        rigid_matrix([x_axis[0],y_axis[0],natural_normal[0],origin[0],
                      x_axis[1],y_axis[1],natural_normal[1],origin[1],
                      x_axis[2],y_axis[2],natural_normal[2],origin[2],0.,0.,0.,1.])
        normal=[-v if expected_orientation else v for v in natural_normal]
        tag,end=read_string(chunk,cursor+109)
        scope_id=reference(chunk,end)
        if (chunk[end+19]!=0 or reference(chunk,end+20)!=expected_owner
                or chunk[end+31:end+33]!=b'\0\1'):
            raise ValueError('Datum plane cache reciprocal feature ownership mismatch')
        if expected_owner not in primary:raise ValueError('Datum plane cache owner missing')
        name,end_name=read_string(chunk,end+33)
        if len(chunk)-end_name!=41:
            raise ValueError('Unobserved datum plane cache footer size')
        return {'native_plane_object_id':identity,'class_guid':PLANE,'record_offset':record.start,
                'owner_feature_object_id':expected_owner,'scope_reference_object_id':scope_id,
                'stored_index':struct.unpack_from('<Q',chunk,end+11)[0],'stored_tag':tag,'stored_name':name or None,
                'stored_mode_code':1,'stored_orientation_flag':expected_orientation,
                'origin_cm':origin,'x_axis':x_axis,'y_axis':y_axis,'normal':normal,
                'cached_plane_to_component_matrix':[x_axis[0],y_axis[0],normal[0],origin[0],
                    x_axis[1],y_axis[1],normal[1],origin[1],x_axis[2],y_axis[2],normal[2],origin[2],0.,0.,0.,1.],
                'geometry_scope':'Stored oriented plane cache; reflected-geometry regeneration is not applied. Flag1 reverses cross(x_axis,y_axis) normal, corroborated by XY/XZ actual API plane getters.'}
    source_owner=selected['entity'].get('feature_object_id')
    if source_owner is None:raise ValueError('Datum Mirror named source feature ownership unavailable')
    source=plane_cache(source_id,source_owner,0)
    output=plane_cache(output_id,owner,1)
    if not same(source['origin_cm'],selected['entity']['origin_cm']) or not same(source['normal'],selected['entity']['normal']):
        raise ValueError('Datum Mirror source selection/cache geometry disagree')
    plane_proxy=reference(control,4)
    plane_ids=_proxy(data,typed,plane_proxy,owner)
    if len(plane_ids)!=1:raise ValueError('Datum Mirror support plane count unsupported')
    plane=_known_descriptor(typed,plane_ids[0],owner,known,263)
    return {'feature_object_id':owner,'feature_class_guid':MIRROR_DATUM,
            'status':'ObservedExplicitDatumOutputAssociationAndCache',
            'control_record_object_id':control_id,'source_association_object_id':source_association_id,
            'output_association_object_id':output_association_id,'source_selection':selected,
            'source_plane':source,'output_plane':output,'mirror_plane':plane,
            'association':'Owned input association identifies source; output association repeats raw source ID, explicitly references output native plane, and reciprocally references the same control; output plane reciprocally owns Mirror feature',
            'api_availability_scope':'Actual resultFeatures returnsNone; output plane timelineObject and definition getters fail. Independent construction-plane collection geometry validates caches only.',
            'scope':'Native source/output ownership and oriented plane caches; arbitrary datum types, general reflection computation and lifecycle replay unresolved'}


def validate_fixtures(root,zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records
    folder=root/'mirrorassemblydatum-65c867cc41d9'
    truth=json.loads((folder/'ground_truth.json').read_text())
    assert len(truth['samples'])==2 and len(truth['errors'])==2 and (folder/'complete.txt').is_file()
    report={'api_version':truth['fusion_version'],'samples':[],'negative_checks':[],
            'interface':'decode_mirror_datum_outputs(data,records,body,feature,known)',
            'initial_nested_failures':truth['errors'],
            'initial_nested_failure_scope':'Both nested cases failed before Mirror creation on optional native entityToken API getter; no nested decoding claim from this folder.',
            'validation_command':'python3 decode_mirror_datum_outputs.py --validate --zstd-library <local libzstd path>'}
    for sample in truth['samples']:
        assert sample['case'].startswith('plane_')
        assert {e['field'] for e in sample['getter_errors']}=={'plane.timelineObject','plane.definition.type'}
        archive=folder/sample['file'];stream=decode_basics(archive,zstd_library)['streams'][0]
        members=read_members(archive,zstd_library);data=members[stream['member']]
        records,_=design_records(data,members.get(stream['member'].replace('BulkStream.dat','MetaStream.dat')))
        by={r.object_id:r for r in records if r.is_primary}
        feature=next(f for f in stream['features'] if f.get('name')=='ProbeMirrorAssemblyDatum')
        record=by[feature['object_id']];body=data[record.body:record.end]
        known=known_construction_entities(data,records,stream['features'])
        result=decode_mirror_datum_outputs(data,records,body,feature,known)
        source=result['source_plane'];output=result['output_plane'];actual_source=sample['actual_inputs'][0]
        # Collection order is an independent API observation, not a native-ID
        # mapping. Exact output identity above comes only from stored references.
        actual_source_collection=[p for p in sample['construction_planes_after'] if p['name']==actual_source['name']]
        actual_other=[p for p in sample['construction_planes_after'] if p['name']!=actual_source['name']]
        checks={'exact_metadata_class_guid_verified':record.class_guid==MIRROR_DATUM,
                'source_cached_origin_normal_match_actual_input':same(source['origin_cm'],actual_source['origin_cm']) and same(source['normal'],actual_source['normal']),
                'source_stored_name_matches_actual_input':source['stored_name']==actual_source['name'],
                'native_output_owned_by_mirror':output['owner_feature_object_id']==feature['object_id'],
                'independent_api_collection_has_one_other_plane':len(actual_other)==1 and len(actual_source_collection)==1,
                'output_cache_matches_independent_other_plane_geometry':len(actual_other)==1 and same(output['origin_cm'],actual_other[0]['origin_cm']) and same(output['normal'],actual_other[0]['normal']),
                'output_cache_matrix_matches_independent_API_transform':len(actual_other)==1 and same(output['cached_plane_to_component_matrix'],actual_other[0]['transform']),
                'actual_resultFeatures_returned_null':sample['api_result_features']['status']=='returned_null',
                'failed_output_timeline_and_definition_not_invented':len(actual_other)==1 and actual_other[0]['timeline'] is None and actual_other[0]['definition_type'] is None}
        assert all(checks.values()),(sample['file'],checks)
        report['samples'].append({'archive':str(archive.relative_to(root)),'checks':checks,'decoded':result,
            'actual_source':actual_source,'independent_actual_after_planes':sample['construction_planes_after'],
            'actual_getter_errors':sample['getter_errors'],'actual_resultFeatures':sample['api_result_features']})
        negative_case=data,records,feature,known,by,result
    data,records,feature,known,by,result=negative_case
    output_record=by[result['output_plane']['native_plane_object_id']]
    output_body=data[output_record.body:output_record.end]
    _,cursor=attributes(output_body,2);_,end=read_string(output_body,cursor+109)
    mutations=[('Output association raw source identity mismatch',result['output_association_object_id'],6,struct.pack('<Q',999999)),
               ('Output association reciprocal control owner mismatch',result['output_association_object_id'],39,struct.pack('<Q',999999)),
               ('Output plane reciprocal Mirror owner mismatch',output_record.object_id,end+21,struct.pack('<Q',999999)),
               ('Unsupported output oriented-normal flag',output_record.object_id,cursor+20,b'\2')]
    for label,identity,offset,replacement in mutations:
        record=by[identity];changed=bytearray(data);changed[record.body+offset:record.body+offset+len(replacement)]=replacement
        feature_record=by[feature['object_id']]
        try:decode_mirror_datum_outputs(bytes(changed),records,data[feature_record.body:feature_record.end],feature,known)
        except (ValueError,KeyError,IndexError,struct.error) as error:
            report['negative_checks'].append({'check':label,'passed':True,'reason':str(error)})
        else:raise AssertionError(label)
    report['limitations']=['Two independent API collection plane geometries corroborate native output caches; exact native source/output identities and ownership come from stored references, never geometry matching.',
                           'No actual resultFeatures members or valid output timeline/definition getter; those unavailable APIs are preserved honestly.',
                           'Cached orientation flag0/1 is observed in source/output planes across XY/XZ; other plane kinds, context frames, output associations and general reflection replay unsupported.',
                           'The two initial nested failures remain intact; nested retry is separately coordinated.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate',required=True,action='store_true')
    parser.add_argument('--zstd-library',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).with_name('mirror-datum-output-decoding.json'))
    args=parser.parse_args();report=validate_fixtures(Path(__file__).resolve().parent,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'samples':len(report['samples']),'negative_checks':len(report['negative_checks']),'output':str(args.output)}))
