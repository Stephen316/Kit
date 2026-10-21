"""Observed asymmetric-fillet offset reversal, reusing common edge-set parsing."""
import math
import struct

from decode_edge_tools import decode_edge_tool
from decode_sketch import reference

FILLET='A07D5F17-68CB-464D-9935-BF68E98A865F'
SCOPE='Native asymmetric-fillet offset reversal and existing common settings; selected ASM edge orientation and offset directions in world geometry remain unresolved'


def decode_asymmetric_radius_payload(chunk,value):
    """Shared-reader opt-in callback; common owner/index/trailer checks stay shared."""
    if (len(chunk)!=88 or chunk[:5]!=b'\0\0\1\0\0' or chunk[5] not in (0,1)
            or chunk[6] not in (0,1) or chunk[7] not in (0,1) or chunk[8:10]!=bytes(2)
            or chunk[21]!=0 or chunk[44:69]!=bytes(25)):
        raise ValueError('Unsupported asymmetric fillet mode/flip framing')
    one,two=value(reference(chunk,22),'EdgeOffset1'),value(reference(chunk,33),'EdgeOffset2')
    if any(not math.isfinite(v['value']) or v['value']<=0 for v in (one,two)):
        raise ValueError('Asymmetric fillet offsets must be positive finite')
    if one['binding_object_id']==two['binding_object_id']:
        raise ValueError('Asymmetric fillet offset bindings repeat')
    return {'kind':'AsymmetricFilletEdgeSet','offsetOne':one,'offsetTwo':two,
            'isFlipped':bool(chunk[5]),
            'flip_scope':'Observed native boolean reverses API offset directions; no world/ASM side mapping inferred'},reference(chunk,10),73


def decode_asymmetric_fillet(data,records,body,feature):
    if feature.get('kind')!='Fillet' or feature.get('class_guid')!=FILLET:
        raise ValueError('Asymmetric fillet requires typed native Fillet')
    matches=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
    if len(matches)!=1 or matches[0].class_guid!=FILLET or data[matches[0].body:matches[0].end]!=body:
        raise ValueError('Asymmetric fillet native feature identity/payload disagrees')
    return decode_edge_tool(data,records,body,feature,asymmetric_radius_decoder=decode_asymmetric_radius_payload)


def decode_asymmetric_fillet_flips(data,records,features):
    decoded,unresolved=[],[]
    for feature in features:
        if feature.get('kind')!='Fillet' or feature.get('class_guid')!=FILLET or not any(p.get('role') in ('EdgeOffset1','EdgeOffset2') for p in feature.get('parameters',[])):
            continue
        try:
            matches=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
            if len(matches)!=1:raise ValueError('Asymmetric fillet feature record ambiguous')
            record=matches[0];body=data[record.body:record.end]
            # Native feature type follows the counted edge-set references. Rule
            # and FullRound share the Fillet class and offset parameter roles,
            # but have separate owned definitions/readers; they are not failed
            # simple edge sets. Leave unknown/malformed types diagnostic.
            if body[:2]==bytes(2) and len(body)>=6:
                count=struct.unpack_from('<I',body,2)[0];cursor=6+11*count
                if 1<=count<=1024 and len(body)>=cursor+4 and struct.unpack_from('<I',body,cursor)[0] in (1,2):
                    continue
            settings=decode_asymmetric_fillet(data,records,body,feature)
            if not any(s['kind']=='AsymmetricFilletEdgeSet' for s in settings['edge_sets']):
                raise ValueError('Offset roles have no asymmetric fillet definition')
            decoded.append({'feature_object_id':feature['object_id'],'tool_settings':settings,'scope':SCOPE})
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:
            unresolved.append({'feature_object_id':feature['object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
