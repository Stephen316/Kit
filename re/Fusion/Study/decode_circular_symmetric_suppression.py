"""Bounded symmetric circular suppression IDs, separate from physical placement.

Only the actual four/five-element ordinal tables and non-seed entries
qualify full settings after controlled API ID contrasts. The even four-element seed-ordinal counterexample stays
partial: its API suppression flag does not reduce native result references.
"""
import math
import struct

from decode_circular_patterns import FEATURE,CONTROL,ELEMENT,decode_circular_pattern
from decode_selection import known_construction_entities,resolve_native_selection,native_proxy_references
from decode_sketch import reference

SCOPE='Captured symmetric circular suppression control IDs only; cache/API transform discrepancies, exact topology, physical suppression of seed ordinal and regeneration remain unresolved'


def resolve_symmetric_suppression(quantity,element_ordinals,suppressed):
    expected={4:[4,2,1,3],5:[4,2,1,3,5]}
    if (quantity not in expected or element_ordinals!=expected[quantity] or not suppressed
            or len(suppressed)!=1 or any(i not in element_ordinals or i==1 for i in suppressed)
            or (quantity==4 and suppressed!=[4])):
        raise ValueError('Symmetric circular suppression table/ordinals outside captured non-seed contrasts')
    return [element_ordinals.index(i) for i in suppressed], 'Observed symmetric quantity4/5 API IDs are indices into the explicit native element-reference table; seed ordinal1 physical suppression remains unsupported'


def inspect_circular_suppression(data,records,feature):
    """Narrow typed controller/list framing; no API or geometry association guessed."""
    def typed(identity,guid):
        rows=[r for r in records if r.is_primary and r.object_id==identity]
        if len(rows)!=1 or rows[0].class_guid!=guid:raise ValueError('Circular suppression typed identity missing/ambiguous')
        record=rows[0];return record,data[record.body:record.end]
    record,body=typed(feature['object_id'],FEATURE)
    if body[:6]!=bytes.fromhex('000100000000'):raise ValueError('Circular suppression feature prefix unsupported')
    control_id=reference(body,6);control,payload=typed(control_id,CONTROL)
    if (len(payload)<106 or payload[:2]!=bytes(2) or payload[2] not in (0,1)
            or payload[25:37]!=bytes(12) or payload[45:49]!=b'\xff'*4 or payload[49] not in (0,1)
            or struct.unpack_from('<I',payload,37)[0] not in (0,1,2)
            or struct.unpack_from('<I',payload,41)[0] not in (1,2)):
        raise ValueError('Circular suppression controller header unsupported')
    pairs=struct.unpack_from('<I',payload,50)[0]
    if not 1<=pairs<=1023 or 54+16*pairs+4>len(payload):raise ValueError('Circular suppression ordinal table bounds disagree')
    cursor=54+16*pairs;quantity=struct.unpack_from('<I',payload,cursor)[0]
    if quantity!=pairs+1 or [struct.unpack_from('<Q',payload,54+16*i)[0] for i in range(pairs)]!=list(range(2,quantity+1)):
        raise ValueError('Circular suppression quantity/ordinal sequence disagrees')
    identities=[reference(payload,cursor+4+11*i) for i in range(quantity)];ordinals=[]
    if len(set(identities))!=quantity:raise ValueError('Circular suppression element references duplicate')
    for identity in identities:
        _,element=typed(identity,ELEMENT)
        if len(element)!=17 or element[:2]!=bytes(2) or reference(element,6)!=control_id:
            raise ValueError('Circular suppression element/controller ownership disagrees')
        ordinals.append(struct.unpack_from('<I',element,2)[0])
    if sorted(ordinals)!=list(range(1,quantity+1)):raise ValueError('Circular suppression element ordinals do not cover quantity')
    cursor+=4+11*quantity
    if reference(payload,cursor+11)!=feature['object_id']:raise ValueError('Circular suppression controller owner differs from feature')
    bindings={p['binding_object_id']:p for p in feature.get('parameters',[])}
    quantity_parameter=bindings.get(reference(payload,cursor));angle_parameter=bindings.get(reference(payload,3))
    if (quantity_parameter is None or quantity_parameter['role']!='countU' or quantity_parameter['raw_float64']!=quantity
            or angle_parameter is None or angle_parameter['role']!='TotalAngle' or not math.isfinite(angle_parameter['raw_float64'])):
        raise ValueError('Circular suppression controller numeric parameter roles/count disagree')
    proxy_id=reference(payload,cursor+22);_,proxy=typed(proxy_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    if len(proxy)!=105 or reference(proxy,94)!=feature['object_id']:
        raise ValueError('Circular suppression owned input proxy disagrees')
    _,listing=typed(reference(body,17),'8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF')
    if (len(listing)!=100 or listing[:6]!=bytes(6) or struct.unpack_from('<I',listing,6)[0]!=1
            or reference(listing,36)!=feature['object_id'] or reference(listing,89)!=feature['object_id']):
        raise ValueError('Circular suppression outside captured owned single-body input list')
    descriptor=reference(listing,10);_,selected=typed(descriptor,'9716F783-676D-42E0-93F9-EBF273E7C035')
    if reference(selected,len(selected)-11)!=feature['object_id']:
        raise ValueError('Circular suppression selected body descriptor owner differs')
    proxy_record,_=typed(proxy_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    proxy_descriptors,_=native_proxy_references(data,proxy_record)
    if proxy_descriptors!=[descriptor]:raise ValueError('Circular suppression proxy/collection body descriptor lists differ')
    cursor+=33;count=struct.unpack_from('<I',payload,cursor)[0]
    if count>=quantity or len(payload)!=cursor+4+4*count:raise ValueError('Circular suppression list extent/count disagrees')
    suppressed=list(struct.unpack_from('<'+'I'*count,payload,cursor+4))
    if len(set(suppressed))!=count or any(i not in ordinals for i in suppressed):raise ValueError('Circular suppression ordinals invalid/duplicate')
    return {'feature_object_id':feature['object_id'],'control_object_id':control.object_id,'is_symmetric':bool(payload[2]),
        'quantity':quantity,'axis_selection_record_object_id':reference(payload,14),'total_angle_radians':angle_parameter['raw_float64'],
        'pattern_entity_type_code':struct.unpack_from('<I',payload,41)[0],'element_record_object_ids':identities,'stored_element_ordinals':ordinals,
        'stored_suppressed_element_ordinals':suppressed,'suppression_list_offset':cursor,
        'controller_payload_hex':payload.hex()}


def decode_circular_symmetric_suppression(data,records,features):
    decoded,partial,unresolved=[],[],[];known=known_construction_entities(data,records,features)
    for feature in features:
        if feature.get('kind')!='CircularPattern' or feature.get('class_guid')!=FEATURE:continue
        candidate=False
        try:
            matches=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
            if len(matches)==1:
                native=data[matches[0].body:matches[0].end]
                control_id=reference(native,6)
                controls=[r for r in records if r.is_primary and r.object_id==control_id and r.class_guid==CONTROL]
                if len(controls)==1:
                    control=data[controls[0].body:controls[0].end]
                    candidate=len(control)>2 and control[2]!=0
            info=inspect_circular_suppression(data,records,feature)
            if not info['is_symmetric'] or not info['stored_suppressed_element_ordinals']:continue
            candidate=True
            axis=resolve_native_selection(data,records,info['axis_selection_record_object_id'],known)
            entity=axis.get('entity',{})
            if (info['pattern_entity_type_code']!=2 or not math.isclose(info['total_angle_radians'],math.pi,rel_tol=0,abs_tol=1e-12)
                    or entity.get('kind')!='ConstructionAxis' or entity.get('name')!='Z'
                    or entity.get('origin_cm')!=[0.,0.,0.] or entity.get('direction')!=[0.,0.,1.]
                    or 'origin_container_object_id' not in entity):
                raise ValueError('Symmetric suppression outside captured body/native-Z/pi-angle family')
            record,=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
            body=data[record.body:record.end]
            if info['quantity']==4 and info['stored_element_ordinals']==[4,2,1,3] and info['stored_suppressed_element_ordinals']==[1]:
                result_count=struct.unpack_from('<I',body,32)[0]
                if body[28:32]!=bytes(4) or result_count!=3:raise ValueError('Even symmetric seed-ordinal counterexample result count differs')
                results=[reference(body,36+11*i) for i in range(result_count)]
                for identity in results:
                    matches=[r for r in records if r.is_primary and r.object_id==identity]
                    if len(matches)!=1 or matches[0].class_guid!='D26351F0-5940-4D23-AA20-2C35475A6D9E':raise ValueError('Circular partial result anchor identity disagrees')
                    payload=data[matches[0].body:matches[0].end]
                    if len(payload)!=102 or reference(payload,91)!=feature['object_id']:raise ValueError('Circular partial result anchor owner disagrees')
                partial.append({**info,'mapped_api_suppressed_element_ids':[info['stored_element_ordinals'].index(i) for i in info['stored_suppressed_element_ordinals']],
                    'generated_result_reference_count':result_count,'result_record_object_ids':results,
                    'status':'Suppression flag ID decoded; physical/result suppression unresolved',
                    'counterexample':'Actual API marks ID2 suppressed yet retains four bodies/six generated member faces; native ordinal1 list does not reduce three generated-result references',
                    'scope':'Captured quantity4/table[4,2,1,3]/storedordinal1 only; no full tool settings or applied physical suppression claim'})
                continue
            settings=decode_circular_pattern(data,records,body,feature,known,features,
                symmetric_suppression_resolver=resolve_symmetric_suppression)
            if settings['pattern_entity_type']!='Bodies' or settings['input_count']!=1:
                raise ValueError('Symmetric suppression outside captured single-body context')
            decoded.append({'feature_object_id':feature['object_id'],'tool_settings':settings,'scope':SCOPE})
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:
            if candidate:unresolved.append({'feature_object_id':feature['object_id'],'reason':str(error)})
    return {'decoded':decoded,'partial':partial,'unresolved':unresolved,'scope':SCOPE}
