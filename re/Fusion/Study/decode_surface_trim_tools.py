"""Observed SurfaceTrim face/body tools; selected-cell recipe stays opaque."""
import struct

from decode_selection import native_proxy_references
from decode_sketch import reference
from decode_surface_tools import decode_surface_tool

TRIM='FF1741AE-E78B-4A5F-8418-751899E12F66'
PROXY='2CA5A1CD-C99B-4C9B-91AF-57989148E841'
FACE='5662F619-2281-4AD9-93DC-1FCFDA1062E7'
BODY='9716F783-676D-42E0-93F9-EBF273E7C035'
SCOPE=('Observed SurfaceTrim singleton owned face/body tool source and target selection '
       'references through the common prefix/wrapper/target codec. Full selected-cell recipe bytes remain '
       'opaque; persistent selected topology, general projection/cell semantics, lifecycle and regeneration unresolved.')


def decode_surface_trim_tools(data,records,features):
    """Return decoded/unresolved/scope; rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid=None):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or (guid is not None and rows[0].class_guid!=guid):
            raise ValueError('SurfaceTrim tool typed reference missing, ambiguous or wrong class')
        record=rows[0];return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=TRIM:continue
        candidate=False
        try:
            record,body=typed(feature['object_id'],TRIM)
            proxy,_=typed(reference(body,17),PROXY);descriptors,_=native_proxy_references(data,proxy)
            for identity in descriptors:
                descriptor,payload=typed(identity)
                if descriptor.class_guid in (FACE,BODY):candidate=True
            if not candidate:continue
            if feature.get('record_offset')!=record.start:
                raise ValueError('SurfaceTrim feature metadata differs from native record')
            def resolver(d,rs,identity,owner_feature,known):
                from decode_surface_trim_sources import resolve_surface_trim_source
                return resolve_surface_trim_source(d,rs,identity,owner_feature['object_id'],features)
            settings=decode_surface_tool(data,records,body,{**feature,'kind':'SurfaceTrim'},{},trim_tool_resolver=resolver)
            if settings['tool_selection']['stored_descriptor_count']!=1 or settings['target_selection']['stored_descriptor_count']!=1:
                raise ValueError('Only captured singleton SurfaceTrim tool/target family supported')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='SurfaceTrim',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=TRIM,reason=str(error)))
    return result
