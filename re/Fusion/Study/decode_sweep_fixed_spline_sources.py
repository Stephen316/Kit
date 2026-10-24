"""Owned fixed-NURBS Sweep path source and natural component-frame samples."""
import copy
import struct

from decode_assembly import decode_assembly,SKETCH_BASE_GUID
from decode_loft_composite_guides import _nurbs_derivative
from decode_mesh_contents import _require
from decode_nurbs import nurbs_geometry,evaluate_nurbs
from decode_parameters import read_string
from decode_placement import IDENTITY,rigid_matrix,transform_point,transform_vector
from decode_selection import native_proxy_references,resolve_single_sketch_curve
from decode_sketch import attributes,reference,same

SCOPE=('Observed singleton owned Sweep proxy/descriptor/leaf selecting a native FixedSpline sketch ID/tag; '
       'canonical stored NURBS and typed identity Sketch-to-component frame qualify natural source geometry. '
       'Derived evaluations are separate from API evidence and Sweep traversal; opposition, native/API handle '
       'identity, result geometry, lifecycle and regeneration remain unresolved.')


def resolve_sweep_fixed_spline_path(data,records,path_id,owner_id,features):
    """Primary-path-only callback; existing primitive and rail defaults unchanged."""
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'FixedSpline Sweep typed identity missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    typed(owner_id,'FCBB1707-4450-46B3-9E65-0F61682EA8CA')
    proxy,proxy_payload=typed(path_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    descriptors,props=native_proxy_references(data,proxy)
    _require(not props and len(descriptors)==1,'FixedSpline Sweep source proxy count/attributes differs')
    selected=resolve_single_sketch_curve(data,records,path_id,owner_id,features,('FixedSpline',))
    sketches=[f for f in features if f['kind']=='Sketch' and f['sketch_object_id']==selected['sketch_object_id']]
    _require(len(sketches)==1,'FixedSpline Sweep source sketch ambiguous');sketch=sketches[0]
    curves=[c for c in sketch['geometry'] if c['object_id']==selected['curve_object_id'] and c.get('entity_tag')==selected['curve_entity_tag'] and c['kind']=='FixedSpline']
    _require(len(curves)==1,'FixedSpline Sweep source curve identity ambiguous');curve=curves[0]
    curve_record,curve_payload=typed(curve['object_id'],'D82E012F-6DDD-4AED-BDE1-C0F7F9100B9B')
    primary_props,after_props=attributes(curve_payload,2)
    _require(curve_payload[:2]==b'\0\1' and primary_props.get('crv_primary_id')==selected['curve_entity_tag']
             and primary_props.get('crv_secondary_id')==0 and curve_payload[after_props:]==b'\xff'*8,
             'FixedSpline Sweep native primary tag framing differs')
    geometry_records=[r for r in records if r.object_id==curve['object_id'] and not r.is_primary
                      and r.start==curve['geometry_record_offset'] and r.class_guid=='EE518F9E-9CC3-4424-9CAB-2B92426E5312']
    _require(len(geometry_records)==1,'FixedSpline Sweep geometry continuation ambiguous');geometry_record=geometry_records[0]
    raw_geometry=data[geometry_record.body:geometry_record.end]
    shape,end=nurbs_geometry(raw_geometry,61)
    _require(shape==curve['nurbs'] and len(raw_geometry)-end==123 and raw_geometry[27]==1
             and struct.unpack_from('<I',raw_geometry,23)[0]==0
             and reference(raw_geometry,50)==curve['start_point_id'] and reference(raw_geometry,39)==curve['end_point_id']
             and reference(raw_geometry,len(raw_geometry)-11)==sketch['sketch_object_id'],
             'FixedSpline Sweep canonical/native spline shape or endpoint/owner links differ')
    _require(shape['degree']==3 and not shape['is_periodic'] and shape['parameter_domain']==[0.,1.]
             and (len(shape['control_points_cm']),len(shape['knots']),len(shape['weights'])) in ((4,8,0),(4,8,4),(6,10,0))
             and shape['knots'][:4]==[0.]*4 and shape['knots'][-4:]==[1.]*4
             and (len(shape['knots'])==8 or 0<shape['knots'][4]<shape['knots'][5]<1)
             and not same(curve['start_cm'],curve['end_cm']),'FixedSpline Sweep outside observed open cubic layout')
    typed(sketch['sketch_object_id'],'44A64366-4BD3-4B24-881A-F94C206E8F2D')
    bases=[r for r in records if not r.is_primary and r.object_id==sketch['sketch_object_id'] and r.class_guid==SKETCH_BASE_GUID]
    _require(len(bases)==1,'FixedSpline Sweep native Sketch base ambiguous');base=bases[0];base_payload=data[base.body:base.end]
    name,_=read_string(base_payload,28)
    _require(name==(sketch.get('name') or ''),'FixedSpline Sweep Sketch name differs from canonical source')
    transform_id=reference(base_payload,0);transform,transform_payload=typed(transform_id,'F47A46FB-DA27-4AFA-8A72-1B38FA596E23')
    placement=sketch.get('placement',{})
    _require(len(transform_payload)==15 and transform_payload[:4]==bytes.fromhex('00000100')
             and placement.get('encoding')=='ImplicitIdentity' and placement.get('transform_object_id')==transform_id
             and placement.get('record_offset')==transform.start and placement.get('sketch_to_component_matrix')==IDENTITY,
             'FixedSpline Sweep source placement outside captured canonical identity frame')
    matrix=rigid_matrix(placement['sketch_to_component_matrix']);component_id=reference(transform_payload,len(transform_payload)-11)
    typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    owned_sketch=copy.deepcopy(sketch);decode_assembly(data,records,[owned_sketch])
    _require(owned_sketch.get('component_object_id')==component_id,'FixedSpline Sweep source collection/component ownership disagrees')
    low,high=shape['parameter_domain'];samples=[]
    for fraction in (0.,.25,.5,.75,1.):
        parameter=low+fraction*(high-low);point=evaluate_nurbs(shape,parameter);derivative=_nurbs_derivative(shape,parameter)
        samples.append(dict(parameter_fraction=fraction,parameter=parameter,point_sketch_local_cm=point,
            point_component_cm=transform_point(matrix,point),natural_parameter_derivative_sketch_local=derivative,
            natural_parameter_derivative_component=transform_vector(matrix,derivative)))
    _require(same(samples[0]['point_sketch_local_cm'],curve['start_cm']) and same(samples[-1]['point_sketch_local_cm'],curve['end_cm']),
             'FixedSpline Sweep natural evaluator/endpoints disagree')
    segment=dict(index=0,descriptor_object_id=selected['descriptor_object_id'],terminal_object_id=selected['terminal_object_id'],
        sketch_object_id=selected['sketch_object_id'],sketch_name=sketch.get('name'),curve_object_id=curve['object_id'],
        curve_entity_tag=selected['curve_entity_tag'],kind='FixedSpline',path_is_opposed_to_entity=None)
    evidence=dict(feature_object_id=owner_id,selection=selected,source_nurbs=copy.deepcopy(shape),
        source_start_point_id=curve['start_point_id'],source_end_point_id=curve['end_point_id'],
        native_curve_primary_record_offset=curve_record.start,native_geometry_continuation_record_offset=geometry_record.start,
        stored_curve_primary_payload_hex=curve_payload.hex(),stored_geometry_continuation_payload_hex=raw_geometry.hex(),
        source_sketch_base_record_offset=base.start,source_sketch_collection_object_id=reference(base_payload,len(base_payload)-11),
        native_transform_object_id=transform_id,native_transform_record_offset=transform.start,stored_transform_payload_hex=transform_payload.hex(),
        canonical_placement=copy.deepcopy(placement),source_component_object_id=component_id,
        source_component_association=owned_sketch['component_association'],natural_derived_samples=samples,
        natural_source_parameter_domain=list(shape['parameter_domain']),path_is_opposed_to_entity=None,
        evaluator_scope='Natural full stored NURBS evaluations in sketch-local and native parent-component frame; no API interior-sample verification, Sweep trim/traversal or occurrence/world transform claim',
        direction_scope='Native traversal/opposition unproved; natural knot-domain order is not a Sweep path direction flag',scope=SCOPE)
    return dict(selection_record_object_id=path_id,count=1,segments=[segment],is_closed=False,
        order_scope='One explicitly selected native source; path traversal/opposition unresolved',
        closure_scope='Captured nonperiodic open cubic has distinct natural endpoints; no general native closure flag',
        native_source_evidence=evidence)
