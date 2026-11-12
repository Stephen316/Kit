"""Derived profile portions in an explicitly qualified native component frame.

Local primitive/selector algorithms remain in the existing Circle/Line/Mixed
readers. This adapter independently qualifies native Sketch/transform/component
and BODY frame references, then opts into mapping their derived local points.
No Sketch identity is fabricated and no assembly/world placement is inferred.
"""
import copy
import math
import struct

from asm_records import inspect_asm
from decode_assembly import COMPONENT_GUID, SKETCH_BASE_GUID, SKETCH_COLLECTION_GUID, component_label
from decode_body_properties import decode_body_properties
from decode_brep import decode_topology
from decode_dependencies import decode_dependencies
from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix
from decode_profile_circle_portions import decode_profile_circle_portions
from decode_profile_line_portions import decode_profile_line_portions
from decode_profile_mixed_portions import decode_profile_mixed_portions
from decode_sketch import attributes, numbers, reference

SKETCH='44A64366-4BD3-4B24-881A-F94C206E8F2D'
TRANSFORM='F47A46FB-DA27-4AFA-8A72-1B38FA596E23'
ROOT_COMPONENT='E03784ED-5E19-4E14-B9F2-3B07017018CD'
EPS=1e-9
SCOPE='Qualified nonidentity native rigid Sketch-to-component frames for previously observed local profile-portion algorithms; source-local derived geometry and component points remain separate, with no assembly/world placement or solver claim'


def _family(sketch):
    kinds=[geometry['kind'] for geometry in sketch['geometry'] if geometry['kind']!='Point']
    if kinds and all(kind=='Circle' for kind in kinds):return 'CircleCircle'
    if kinds and all(kind=='Line' for kind in kinds):return 'LineLine'
    if sorted(kinds)==['Circle','Line']:return 'CircleLine'
    return None


def _provider(data,records,features,members):
    groups={}
    for record in records:
        if record.is_primary:groups.setdefault(record.object_id,[]).append(record)
    primary={identity:rows[0] for identity,rows in groups.items() if len(rows)==1}
    def typed(identity,guid):
        record=primary.get(identity)
        if record is None or record.class_guid!=guid:
            raise ValueError('Placed-profile typed native reference missing, ambiguous or wrong class')
        return record,data[record.body:record.end]
    component_bases={}
    for record in records:
        if record.class_guid==COMPONENT_GUID:component_bases.setdefault(record.object_id,[]).append(record)
    components=[component_label(data[rows[0].body:rows[0].end],identity)
                for identity,rows in component_bases.items() if len(rows)==1 and identity in primary]
    component_ids={component['object_id'] for component in components}
    feature_by={feature['object_id']:feature for feature in features}
    dependencies=[{'object_id':feature['object_id']} for feature in features]
    decode_dependencies(data,records,dependencies,{'components':components})
    dependencies={feature['object_id']:feature for feature in dependencies}
    properties=decode_body_properties(data,records,{'components':components})
    topology_cache={}

    def frame(sketch,row):
        native_id=sketch['sketch_object_id'];typed(native_id,SKETCH)
        bases=[record for record in records if record.object_id==native_id and not record.is_primary and record.class_guid==SKETCH_BASE_GUID]
        if len(bases)!=1:raise ValueError('Placed-profile native Sketch base is missing/ambiguous')
        base=bases[0];body=data[base.body:base.end]
        native_name,_=read_string(body,28)
        if native_name!=sketch['name']:raise ValueError('Placed-profile native Sketch name disagrees with canonical feature')
        transform_id=reference(body,0);collection_id=reference(body,len(body)-11)
        transform,transform_body=typed(transform_id,TRANSFORM)
        if len(transform_body)!=143 or transform_body[:3]!=bytes(3) or transform_body[-12]!=0:
            raise ValueError('Placed-profile transform outside observed explicit matrix framing')
        matrix=rigid_matrix(numbers(transform_body,3,16))
        if all(math.isclose(a,b,abs_tol=EPS) for a,b in zip(matrix,IDENTITY)):
            raise ValueError('Identity source placement belongs to the unchanged original readers')
        component_id=reference(transform_body,len(transform_body)-11)
        component_primary,_=typed(component_id,ROOT_COMPONENT)
        component_base=component_bases.get(component_id,[])
        if component_id not in component_ids or len(component_base)!=1:
            raise ValueError('Placed-profile matrix component definition unresolved')
        placement=sketch.get('placement',{})
        if (placement.get('sketch_to_component_matrix')!=matrix or placement.get('transform_object_id')!=transform_id
                or placement.get('record_offset')!=transform.start or placement.get('encoding')!='ExplicitFloat64Matrix'):
            raise ValueError('Canonical Sketch placement differs from typed native matrix/source reference')
        _,collection=typed(collection_id,SKETCH_COLLECTION_GUID)
        props,cursor=attributes(collection,2)
        if 'crv_tag_id_idx' not in props:raise ValueError('Placed-profile source Sketch collection attribute framing unsupported')
        count=struct.unpack_from('<I',collection,cursor)[0];cursor+=4
        if not 1<=count<=100000 or cursor+11*count>len(collection)-11:
            raise ValueError('Placed-profile Sketch collection membership truncated')
        identities=[reference(collection,cursor+11*i) for i in range(count)]
        if identities.count(native_id)!=1 or reference(collection,len(collection)-11)!=component_id:
            raise ValueError('Placed-profile Sketch collection/component ownership is not reciprocal')
        source_id=row['source_feature_object_id'];source=feature_by[source_id]
        for feature in (sketch,source):
            fresh=dependencies[feature['object_id']]
            if (fresh.get('component_object_id')!=component_id or fresh.get('component_scope_object_id')!=feature.get('component_scope_object_id')
                    or feature.get('component_object_id')!=component_id):
                raise ValueError('Placed-profile feature dependency scope differs from matrix/component owner')
        bodies=[item for item in properties['bodies'] if item['object_id']==row['native_body_object_id']]
        if len(bodies)!=1 or bodies[0].get('component_object_id')!=component_id or 'collection_object_id' not in bodies[0]:
            raise ValueError('Placed-profile native BODY lacks reciprocal ownership in the source component')
        blob_member=row['history_blob_member']
        if blob_member not in topology_cache:topology_cache[blob_member]=decode_topology(inspect_asm(members[blob_member]))
        topology=topology_cache[blob_member]
        if topology['unresolved']:raise ValueError('Placed-profile stored BODY topology incomplete')
        graphs=[graph for graph in topology['body_graphs'] if graph['body_index']==row['asm_body_index']]
        if len(graphs)!=1 or graphs[0]['body_transform_is_identity'] is not True:
            raise ValueError('Placed-profile BODY frame is not a qualified identity component cache')
        graph=graphs[0];transform_index=graph['transform_index'];nodes={node['index']:node for node in topology['nodes']}
        body_transform=nodes.get(transform_index)
        if body_transform is None or body_transform['kind']!='transform' or body_transform['is_observed_identity'] is not True:
            raise ValueError('Placed-profile explicit stored BODY identity transform is missing')
        return {'status':'QualifiedNativeSketchToComponentFrame',
            'sketch_to_component_matrix':list(matrix),'matrix_order':'row-major; column-vector multiplication','translation_units':'cm',
            'native_sketch_object_id':native_id,'native_sketch_base_class_guid':SKETCH_BASE_GUID,
            'native_sketch_base_record_offset':base.start,'native_sketch_collection_object_id':collection_id,
            'native_transform_object_id':transform_id,'native_transform_class_guid':TRANSFORM,'native_transform_record_offset':transform.start,
            'native_component_object_id':component_id,'native_component_primary_class_guid':component_primary.class_guid,
            'native_component_base_class_guid':COMPONENT_GUID,'native_component_base_record_offset':component_base[0].start,
            'source_feature_object_id':source_id,
            'sketch_feature_component_scope_object_id':dependencies[sketch['object_id']]['component_scope_object_id'],
            'source_feature_component_scope_object_id':dependencies[source_id]['component_scope_object_id'],
            'native_body_object_id':row['native_body_object_id'],'native_body_collection_object_id':bodies[0]['collection_object_id'],
            'stored_BODY_frame':{'history_blob_member':blob_member,'asm_body_record_index':graph['body_index'],
                'asm_identity_transform_record_index':transform_index,'stored_vectors':copy.deepcopy(body_transform['stored_vectors']),
                'stored_scale':body_transform['stored_scale'],'stored_flags':copy.deepcopy(body_transform['stored_flags'])},
            'coordinate_scope':'Native source parent-component coordinates only; no assembly occurrence/world placement',
            'direction_basis':'Canonical native Sketch-to-component matrix; independently measured API basis corroboration belongs to validation, not a transform-label assumption'}
    return frame


def decode_placed_profile_portions(data,records,features,member,members,body_identifier_summary):
    sketches={feature['sketch_object_id']:feature for feature in features if feature['kind']=='Sketch'}
    owners={}
    for feature in features:
        if feature['kind']!='Extrude' or len(feature.get('sketch_reference_candidates',[]))!=1:continue
        sketch=sketches.get(feature['sketch_reference_candidates'][0]['sketch_object_id'])
        if sketch is None:continue
        matrix=sketch.get('placement',{}).get('sketch_to_component_matrix')
        if matrix is None or len(matrix)!=16 or all(math.isclose(a,b,abs_tol=EPS) for a,b in zip(matrix,IDENTITY)):continue
        family=_family(sketch)
        if family is not None:owners[feature['object_id']]=family
    if not owners:return {'decoded':[],'unresolved':[],'scope':SCOPE}
    try:provider=_provider(data,records,features,members)
    except (ValueError,KeyError,IndexError,TypeError,ArithmeticError,UnicodeError,struct.error) as error:
        return {'decoded':[],'unresolved':[{'source_feature_object_id':identity,'reason':str(error)} for identity in owners],'scope':SCOPE}
    decoders={'CircleCircle':decode_profile_circle_portions,'LineLine':decode_profile_line_portions,'CircleLine':decode_profile_mixed_portions}
    decoded=[];unresolved=[]
    for family,decoder in decoders.items():
        ids={identity for identity,value in owners.items() if value==family}
        if not ids:continue
        selected=[feature for feature in features if feature['kind']!='Extrude' or feature['object_id'] in ids]
        result=decoder(data,records,selected,member,members,body_identifier_summary,source_frame=provider)
        for row in result['decoded']:
            row['placed_profile_family']=family;decoded.append(row)
        unresolved.extend(result['unresolved'])
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
