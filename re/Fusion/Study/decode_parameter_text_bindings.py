"""Captured second editable SketchText parameter binding, with explicit ownership.

The binding's u32 at16 is a slot, not a Text value-type discriminator. Only the
saved second-Text slot3/height-slot2 case is extended; other variants stay strict.
"""

import re
import struct

from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference, same

PARAMETER = '7A6A3D31-BE74-4E19-9115-20642944C2E4'
TEXT_BINDING = 'e5460b7b-000b-4a70-ab52-4c2fcc470eb2'
HEIGHT_BINDING = 'D91D429C-1BB5-4640-B49F-69AF14F463E9'
TEXT = 'E0618268-3A06-450E-9E94-7CF4C2E66802'
SKETCH = '8DA771B7-52ED-42FC-94E2-2353FE141373'
BOOKKEEPING = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'


def validate_numbered_text_binding(data, records, binding_id, parameter_id, text, stored_index):
    """Return canonical binding metadata for the captured second Text only.

    Safe for a decode_parameters fallback: does not call decode_stream, alter
    caller bytes, or require the later full sketch/font/glyph readers.
    """
    grouped = {}
    for r in records:
        if r.is_primary:
            grouped.setdefault(r.object_id,[]).append(r)
    primary = {i:rs[0] for i,rs in grouped.items() if len(rs)==1}

    def typed(identity,guid):
        r=primary.get(identity)
        if r is None or r.class_guid != guid:
            raise ValueError('Numbered Text typed reference missing, ambiguous or wrong class')
        return r,data[r.body:r.end]

    def parameter(identity):
        _,b=typed(identity,PARAMETER)
        if b[:12] != bytes(7)+b'\6\0\0\0\0':
            raise ValueError('Unsupported numbered Text model parameter header')
        comment,c=read_string(b,12,allow_text_controls=True)
        index=struct.unpack_from('<I',b,c)[0];binding=reference(b,c+4)
        expression,c=read_string(b,c+15,allow_text_controls=True)
        metadata=b[c:c+10];c+=10
        role,c=read_string(b,c);value,c=read_string(b,c,allow_text_controls=True)
        units,c=read_string(b,c);name,c=read_string(b,c)
        if len(metadata)!=10 or len(b)!=c+20 or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name):
            raise ValueError('Unsupported numbered Text model parameter fields')
        if b[-12] != 0:
            raise ValueError('Unsupported numbered Text parameter collection marker')
        collection=reference(b,len(b)-11)
        typed(collection,'B0556F58-EE09-46A7-B18F-E296F48E5B13')
        return {'index':index,'binding':binding,'expression':expression,'metadata':metadata,'role':role,
                'value':value,'units':units,'name':name,'numeric':b[c:c+8],'collection':collection}

    def binding(identity,guid,expected_owner,expected_value,slot):
        r,b=typed(identity,guid)
        if (b[:5] != bytes.fromhex('0101000000') or reference(b,5)!=expected_owner
                or struct.unpack_from('<I',b,16)[0]!=slot or b[20]!=0):
            raise ValueError('Numbered Text binding slot/owner/prefix disagrees')
        if guid==TEXT_BINDING:
            value,c=read_string(b,21,allow_text_controls=True)
            if value!=expected_value:
                raise ValueError('Numbered Text cached text disagrees')
        else:
            value,c=numbers(b,21,1)[0],29
            if not same([value],[expected_value]):
                raise ValueError('Numbered Text cached height disagrees')
        if len(b)!=c+56 or b[c+15:c+19]!=bytes(4) or b[c+30:c+33]!=b'\1\0\0' or b[c+44]!=0:
            raise ValueError('Unsupported numbered Text binding suffix')
        parameter_id=reference(b,c);index=struct.unpack_from('<I',b,c+11)[0]
        if reference(b,c+19)!=expected_owner or reference(b,c+45)!=expected_owner:
            raise ValueError('Numbered Text repeated binding owner disagrees')
        book_id=reference(b,c+33);_,book=typed(book_id,BOOKKEEPING)
        if len(book)!=39 or reference(book,12)!=identity:
            raise ValueError('Numbered Text binding bookkeeping backlink disagrees')
        return r,parameter_id,index,book_id

    record,b=typed(binding_id,TEXT_BINDING)
    if b[:5]!=bytes.fromhex('0101000000') or struct.unpack_from('<I',b,16)[0]!=3 or b[20]!=0:
        raise ValueError('Only captured second-Text numbered binding slot3 is supported')
    owner=reference(b,5);_,feature=typed(owner,SKETCH)
    count=struct.unpack_from('<I',feature,3)[0]
    if count!=4:
        raise ValueError('Only captured two-Text/four-binding sketch owner supported')
    bindings=[reference(feature,7+11*i) for i in range(count)]
    if len(set(bindings))!=4 or bindings[3]!=binding_id:
        raise ValueError('Second Text binding does not occupy explicit sketch binding slot3')
    sketch_id=reference(feature,12+11*count)
    candidates=[]
    for source in primary.values():
        if source.class_guid!=TEXT:
            continue
        raw=data[source.body:source.end]
        try:
            props,c=attributes(raw,2)
            if (raw[:2]!=b'\0\1' or set(props)!={'EntityGenesis','textex_tag','txt_tag_base'}
                    or props['EntityGenesis']!=0 or type(props['txt_tag_base']) is not int or props['txt_tag_base']<0):
                continue
            font,c=read_string(raw,c+25)
            if not font or raw[c]!=0:
                continue
            height=numbers(raw,c+1,1)[0];height_binding=reference(raw,c+9)
            content,end=read_string(raw,c+27,allow_text_controls=True)
            if reference(raw,end)!=binding_id:
                continue
            if content!=text or height<=0 or reference(raw,len(raw)-11)!=sketch_id or height_binding!=bindings[2]:
                raise ValueError('Second Text source/height binding/sketch owner disagrees')
            candidates.append((source,props,height,height_binding))
        except (IndexError,struct.error,UnicodeError):
            continue
    if len(candidates)!=1:
        raise ValueError('Missing or ambiguous explicitly linked second Text source')
    source,props,height,height_binding_id=candidates[0]
    _,text_parameter_id,text_index,book_id=binding(binding_id,TEXT_BINDING,owner,text,3)
    _,height_id,height_index,_=binding(height_binding_id,HEIGHT_BINDING,owner,height,2)
    text_p=parameter(parameter_id);height_p=parameter(height_id)
    if (text_parameter_id!=parameter_id or text_index!=stored_index or text_p['index']!=stored_index
            or text_p['binding']!=binding_id or text_p['role']!='Text2-Text' or text_p['value']!=text
            or text_p['units']!='Text' or text_p['metadata']!=b'\1'+bytes(9) or text_p['numeric']!=bytes(8)):
        raise ValueError('Second Text parameter role/index/type/value binding disagrees')
    if (height_p['index']!=height_index or height_p['binding']!=height_binding_id or height_p['role']!='Text2-Height'
            or height_p['value'] or height_p['units']!='mm' or height_p['metadata']!=bytes(10)
            or not same(list(struct.unpack('<d',height_p['numeric'])),[height]) or height_p['collection']!=text_p['collection']):
        raise ValueError('Second Text reciprocal height parameter disagrees')
    return {'binding_owner_object_id':owner,'binding_offset':record.start,
            'binding_bookkeeping_object_id':book_id,'binding_value_representation':'UTF16LE',
            'binding_status':'Captured second editable Text: explicit source, ordered sketch slots2/3 and reciprocal Text2 height/text parameters',
            'binding_slot':3,'binding_text_source_object_id':source.object_id,
            'binding_height_parameter_object_id':height_id,'binding_height_object_id':height_binding_id,
            'binding_source_sketch_object_id':sketch_id,
            'opaque_text_tag_base':props['txt_tag_base'],
            'opaque_text_tag_base_status':'Retained only; glyph and font index semantics unresolved'}
