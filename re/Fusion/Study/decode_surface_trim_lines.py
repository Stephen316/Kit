"""Observed SurfaceTrim sketch-Line tools; selected-cell recipe stays opaque."""
import struct

from decode_selection import native_proxy_references
from decode_sketch import reference
from decode_surface_tools import decode_surface_tool
from decode_surface_trim_tools import TRIM,PROXY

DESCRIPTOR='5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
LEAF='E2CEFD18-D755-4E09-8E7F-953A2F6D43F8'
SCOPE=('Observed SurfaceTrim singleton native sketch-Line tool with typed proxy/descriptor/sketch-tag '
       'source and canonical parent-component geometry. Common recipe/target ownership retained; line '
       'orientation/offset does not assign selected-cell meaning, projected trim sides or persistent topology. '
       'General curves, lifecycle and regeneration unresolved.')


def decode_surface_trim_lines(data,records,features):
    """Return decoded/unresolved/scope; rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid=None):
        matches=grouped.get(identity,[])
        if len(matches)!=1 or (guid is not None and matches[0].class_guid!=guid):
            raise ValueError('SurfaceTrim Line typed reference missing, ambiguous or wrong class')
        record=matches[0];return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=TRIM:continue
        candidate=False
        try:
            record,body=typed(feature['object_id'],TRIM)
            proxy,_=typed(reference(body,17),PROXY);ids,_=native_proxy_references(data,proxy)
            for identity in ids:
                descriptor,payload=typed(identity)
                if descriptor.class_guid==DESCRIPTOR and typed(reference(payload,2))[0].class_guid==LEAF:candidate=True
            if not candidate:continue
            if feature.get('record_offset')!=record.start:
                raise ValueError('SurfaceTrim Line feature metadata differs from native record')
            def resolver(d,rs,identity,owner_feature,known):
                from decode_surface_trim_line_sources import resolve_surface_trim_line_source
                return resolve_surface_trim_line_source(d,rs,identity,owner_feature['object_id'],features)
            settings=decode_surface_tool(data,records,body,{**feature,'kind':'SurfaceTrim'},{},trim_tool_resolver=resolver,
                allowed_trim_tool_kinds=('SketchLine',))
            if settings['tool_selection']['stored_descriptor_count']!=1 or settings['target_selection']['stored_descriptor_count']!=1:
                raise ValueError('Only captured singleton SurfaceTrim Line/target family supported')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='SurfaceTrim',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=TRIM,reason=str(error)))
    return result
