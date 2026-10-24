"""Observed SplitBody Patch-sheet tools through unchanged common split controls."""
import struct

from decode_selection import native_proxy_references
from decode_sketch import reference
from decode_split import decode_split

SPLIT='65CA3206-E33A-471E-8E40-2C72B57C6181'
PROXY='2CA5A1CD-C99B-4C9B-91AF-57989148E841'
FACE='5662F619-2281-4AD9-93DC-1FCFDA1062E7'
BODY='9716F783-676D-42E0-93F9-EBF273E7C035'
SCOPE=('Observed one-target SplitBody with independent owned Patch-sheet face/body tool descriptors, '
       'literal extension boolean and operation-flag agreement, typed historical source/tool and owned '
       'result routes. Selected ASMface identity, general sheet extension, lifecycle and regeneration unresolved.')


def decode_split_body_sheet_tools(data,records,features):
    """Return decoded/unresolved/scope; successful rows require a qualified tool."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid=None):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or (guid is not None and rows[0].class_guid!=guid):
            raise ValueError('Split sheet tool typed reference missing, ambiguous or wrong class')
        record=rows[0];return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=SPLIT:continue
        candidate=False
        try:
            record,body=typed(feature['object_id'],SPLIT)
            proxy,_=typed(reference(body,34),PROXY)
            descriptors,_=native_proxy_references(data,proxy)
            if not any(typed(i)[0].class_guid in (FACE,BODY) for i in descriptors):continue
            candidate=True
            if feature.get('record_offset')!=record.start:
                raise ValueError('Split sheet tool feature metadata differs from native record')
            from decode_split_body_sheet_routes import resolve_split_body_sheet_tool
            settings=decode_split(data,records,body,{**feature,'kind':'SplitBody'},{},tool_resolver=resolve_split_body_sheet_tool)
            if settings['input_body_count']!=1 or settings['tool'] is None:
                raise ValueError('Only captured singleton SplitBody sheet tool family supported')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='SplitBody',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=SPLIT,reason=str(error)))
    return result
