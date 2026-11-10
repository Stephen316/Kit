"""Observed two-target SplitBody sheet controls; source/result groups remain unpaired."""
import struct

from decode_selection import native_proxy_references
from decode_sketch import reference
from decode_split import decode_split
from decode_split_body_sheet_tools import SPLIT,PROXY,FACE,BODY

SCOPE=('Observed two-target SplitBody with independent owned Patch-sheet face/body tool descriptors, '
       'literal extension boolean and matching operation flag. Ordered historical source descriptors, '
       'ordered newly owned anchors and current BODY collection are retained separately; source/result '
       'pairing, selected ASMface identity, general extension, lifecycle and regeneration unresolved.')


def decode_split_body_multi_sheet_tools(data,records,features):
    """Return decoded/unresolved/scope for the independently qualified count2 family."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid=None):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or (guid is not None and rows[0].class_guid!=guid):
            raise ValueError('Multi-target split sheet typed reference missing, ambiguous or wrong class')
        record=rows[0];return record,data[record.body:record.end]
    for feature in features:
        if feature.get('class_guid')!=SPLIT:continue
        candidate=False
        try:
            record,body=typed(feature['object_id'],SPLIT)
            if struct.unpack_from('<I',body,49)[0]==1:continue
            proxy,_=typed(reference(body,34),PROXY)
            descriptors,_=native_proxy_references(data,proxy)
            if not any(typed(i)[0].class_guid in (FACE,BODY) for i in descriptors):continue
            candidate=True
            if feature.get('record_offset')!=record.start:
                raise ValueError('Multi-target split sheet feature metadata differs from native record')
            from decode_split_body_multi_sheet_routes import resolve_split_body_multi_sheet_tool
            settings=decode_split(data,records,body,{**feature,'kind':'SplitBody'},{},tool_resolver=resolve_split_body_multi_sheet_tool)
            if settings['input_body_count']!=2 or settings['tool'] is None:
                raise ValueError('Only captured two-target SplitBody sheet tool family supported')
            result['decoded'].append(dict(feature_object_id=feature['object_id'],kind='SplitBody',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error) as error:
            if candidate:result['unresolved'].append(dict(feature_object_id=feature['object_id'],class_guid=SPLIT,reason=str(error)))
    return result
