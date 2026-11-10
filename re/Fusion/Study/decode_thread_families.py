"""Bounded straight cosmetic Thread family controls; shared codec remains default ISO-only."""
import math
import struct

from decode_parameters import decode_stream,read_string
from decode_sketch import reference
from decode_threads import decode_thread
from decode_thread_multi_faces import THREAD,BINDING,PARAMETER
from decode_thread_family_body_routes import resolve_thread_family_faces

FAMILIES=('ANSI Unified Screw Threads','ISO Metric Trapezoidal Threads','BSP Pipe Threads')
SCOPE=('Observed full-length right-handed cosmetic singleton ANSI Unified external, ISO Metric Trapezoidal '
       'external and BSP Pipe internal Thread controls. Common stored dimensions and owned selections retained; '
       'tapered/modeled/plural variants, persistent face identity, family standards and regeneration unresolved.')


def decode_thread_families(data,records,features):
    """Return decoded/unresolved/scope; successful rows expose unchanged common settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        matches=grouped.get(identity,[])
        if len(matches)!=1 or matches[0].class_guid!=guid:
            raise ValueError('Thread family typed reference missing, ambiguous or wrong class')
        record=matches[0];return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=THREAD:continue
        candidate=False
        try:
            record,body=typed(feature['object_id'],THREAD)
            count=struct.unpack_from('<I',body,11)[0]
            if count not in (0,1):continue
            cursor=15+16*count;strings=[]
            for _ in range(5):text,cursor=read_string(body,cursor);strings.append(text)
            if strings[-1] not in FAMILIES:continue
            candidate=True
            if feature.get('record_offset')!=record.start:
                raise ValueError('Thread family feature metadata differs from native record')
            settings=decode_thread(data,records,body,feature,allowed_families=FAMILIES,
                                   selection_resolver=resolve_thread_family_faces)
            if (settings['is_modeled'] or not settings['is_full_length'] or not settings['is_right_handed']
                    or settings['attached_hole_object_id'] is not None or settings['stored_modeled_table_pairs']
                    or settings['is_internal']!=(settings['thread_type']=='BSP Pipe Threads')):
                raise ValueError('Unsupported Thread family mode outside captured straight cosmetic singleton family')
            numeric=('thread_angle_degrees','pitch_cm','major_diameter_cm','minor_diameter_cm','pitch_diameter_cm','stored_length_cm','stored_offset_cm')
            if (not all(math.isfinite(settings[k]) for k in numeric)
                    or settings['stored_length_cm']<=0 or settings['stored_offset_cm']<0):
                raise ValueError('Thread family dimensions/length/offset outside finite physical domain')
            for role,binding_id in settings['parameter_bindings'].items():
                parameters=[p for p in feature.get('parameters',[]) if p.get('binding_object_id')==binding_id and p['role']==role]
                if len(parameters)!=1:raise ValueError('Thread family attached numeric parameter ambiguous')
                parameter=parameters[0];_,binding=typed(binding_id,BINDING)
                pr,_=typed(parameter['parameter_object_id'],PARAMETER);parsed,rejected=decode_stream(data,[pr])
                if (len(parsed)!=1 or rejected or parsed[0]['role']!=role
                        or parsed[0].get('declared_binding_object_id')!=binding_id
                        or parsed[0].get('parameter_object_id')!=parameter['parameter_object_id']
                        or parsed[0]['raw_float64']!=parameter['raw_float64'] or parsed[0]['internal_units']!='cm'
                        or len(binding)!=85 or binding[:6]!=bytes.fromhex('010100000001')
                        or any(reference(binding,o)!=feature['object_id'] for o in (5,48,74))
                        or reference(binding,29)!=parameter['parameter_object_id']
                        or struct.unpack_from('<d',binding,21)[0]!=parameter['raw_float64']):
                    raise ValueError('Thread family numeric binding owner/role/parameter/value copies disagree')
            settings['input_selection_status']='Owned singleton cylindrical-face descriptor and native source recipe retained; API handle and persistent face-to-ASM correspondence unresolved'
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='Thread',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=THREAD,reason=str(error)))
    return result
