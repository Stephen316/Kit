"""Observed ReplaceFace sheet face/body targets through the shared face-edit codec."""
import struct

from decode_face_tools import decode_face_tool
from decode_selection import native_proxy_references
from decode_sketch import reference

REPLACE='8BD31492-18F4-45C9-8512-D720CCFC2450'
PROXY='2CA5A1CD-C99B-4C9B-91AF-57989148E841'
FACE='5662F619-2281-4AD9-93DC-1FCFDA1062E7'
BODY='9716F783-676D-42E0-93F9-EBF273E7C035'
SCOPE=('Observed singleton ReplaceFace source face and distinct target face/body descriptors for an '
       'independent owned Patch sheet, tangent-chain false/true controls and reciprocal historical native '
       'BODY routes. API argument normalization, selected ASM face identity, general targets, lifecycle '
       'and regeneration remain separate or unresolved.')


def decode_replace_face_targets(data,records,features):
    """Return decoded/unresolved/scope; rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid=None):
        matches=grouped.get(identity,[])
        if len(matches)!=1 or (guid is not None and matches[0].class_guid!=guid):
            raise ValueError('ReplaceFace target typed reference missing, ambiguous or wrong class')
        record=matches[0];return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=REPLACE:continue
        candidate=False
        try:
            record,body=typed(feature['object_id'],REPLACE)
            proxy,_=typed(reference(body,7),PROXY)
            descriptors,_=native_proxy_references(data,proxy)
            if not any(typed(i)[0].class_guid in (FACE,BODY) for i in descriptors):continue
            candidate=True
            if feature.get('record_offset')!=record.start:
                raise ValueError('ReplaceFace target feature metadata differs from native record')
            from decode_replace_face_body_routes import resolve_replace_face_target
            common_feature={**feature,'kind':'ReplaceFace'}
            settings=decode_face_tool(data,records,body,common_feature,{},replace_target_resolver=resolve_replace_face_target)
            if len(settings['source_descriptor_object_ids'])!=1:
                raise ValueError('Only captured singleton ReplaceFace source supported')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='ReplaceFace',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=REPLACE,reason=str(error)))
    return result
