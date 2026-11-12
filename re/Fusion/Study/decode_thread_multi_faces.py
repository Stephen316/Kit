"""Observed two-face cosmetic Thread controls through a bounded selection hook."""
import math
import struct

from decode_parameters import decode_stream
from decode_sketch import reference
from decode_threads import decode_thread

THREAD='584D9526-EF22-4F6F-9FE1-5FCF1F3CE575'
BINDING='D91D429C-1BB5-4640-B49F-69AF14F463E9'
PARAMETER='7A6A3D31-BE74-4E19-9115-20642944C2E4'
SCOPE=('Observed two-face cosmetic ISO metric Thread: full external, partial external and full internal controls, '
       'owned plural cylindrical-face descriptors and explicit historical native body recipes. API handle equality '
       'is false in these captures; persistent face/ASM identity, modeled threads and regeneration unresolved.')


class _SingletonThread(ValueError):
    """Leave existing singleton Thread output/diagnostics with the default reader."""


def decode_thread_multi_faces(data,records,features):
    """Return decoded/unresolved/scope, rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or rows[0].class_guid!=guid:raise ValueError('Plural Thread typed reference missing, ambiguous or wrong class')
        record=rows[0]
        return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=THREAD:continue
        activated=[]
        def resolver(d,rs,body,f,cursor):
            count=struct.unpack_from('<I',body,cursor)[0]
            if count==1:raise _SingletonThread()
            activated.append(cursor)
            from decode_thread_body_routes import resolve_thread_multi_faces
            return resolve_thread_multi_faces(d,rs,body,f,cursor)
        try:
            record,body=typed(feature['object_id'],THREAD)
            if feature.get('record_offset')!=record.start:raise ValueError('Plural Thread feature metadata differs from native record')
            settings=decode_thread(data,records,body,feature,selection_resolver=resolver)
            if (settings['is_modeled'] or settings['attached_hole_object_id'] is not None
                    or not settings['is_right_handed'] or (settings['is_internal'] and not settings['is_full_length'])
                    or settings['stored_modeled_table_pairs'] or len(settings['selection_record_object_ids'])!=2):
                raise ValueError('Unsupported plural Thread mode outside observed cosmetic external/full-internal family')
            values=(settings['stored_length_cm'],settings['stored_offset_cm'])
            if not all(math.isfinite(v) for v in values) or values[0]<=0 or values[1]<0:
                raise ValueError('Plural Thread length/offset outside positive finite domain')
            control_evidence=[]
            for role,binding_id in settings['parameter_bindings'].items():
                matches=[p for p in feature.get('parameters',[]) if p.get('binding_object_id')==binding_id and p['role']==role]
                if len(matches)!=1:raise ValueError('Plural Thread attached length/offset parameter ambiguous')
                p=matches[0]
                _,binding=typed(binding_id,BINDING)
                parameter_record,_=typed(p['parameter_object_id'],PARAMETER)
                parsed,rejected=decode_stream(data,[parameter_record])
                if (len(parsed)!=1 or rejected or parsed[0]['role']!=role
                        or parsed[0].get('declared_binding_object_id')!=binding_id or parsed[0].get('parameter_object_id')!=p['parameter_object_id']
                        or parsed[0]['raw_float64']!=p['raw_float64'] or parsed[0]['internal_units']!='cm'
                        or len(binding)!=85 or binding[:6]!=bytes.fromhex('010100000001')
                        or any(reference(binding,o)!=feature['object_id'] for o in (5,48,74))
                        or reference(binding,29)!=p['parameter_object_id']
                        or struct.unpack_from('<d',binding,21)[0]!=p['raw_float64']):
                    raise ValueError('Plural Thread numeric binding owner/role/parameter/value copies disagree')
                control_evidence.append(dict(role=role,binding_object_id=binding_id,parameter_object_id=p['parameter_object_id'],
                    parameter_name=p['parameter_name'],stored_value_cm=p['raw_float64'],display_units=p['display_units'],
                    is_active=not settings['is_full_length'],stored_binding_payload_hex=binding.hex(),
                    scope='Owned native parameter copies only; full-length mode leaves stored length/offset inactive'))
            settings['control_parameter_evidence']=control_evidence
            settings['plural_selection_scope']='Two owned face proxies/descriptors and native historical source recipes; source body list order is independent from current collection order and actual API handles.'
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='Thread',name=feature.get('name'),settings=settings))
        except _SingletonThread:
            continue
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            if activated:
                result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=THREAD,reason=str(error)))
    return result
