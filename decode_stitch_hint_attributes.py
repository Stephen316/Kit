"""Exact terminal stitch_hint EDGE sibling framing, without numeric semantics.

Only the observed EDGE head generic-tag→terminal stitch-hint chain is admitted.
All pointers refer to contiguous initial-geometry record ordinals; three finite
stored doubles are literal data, not decoded tolerances or topology identity.
"""
import math
import struct

NAME='stitch_hint-sys-attrib'
NAME_BYTES=b'\x0e\x0bstitch_hint\x0e\x03sys\x0d\x06attrib'


def decode_stitch_hint_attribute(record,records):
    limit=next((r['index'] for r in records if r['record_kind']=='marker'),len(records))
    if any(r['index']!=i or r['record_kind']!='entity' or r['section']!='geometry' for i,r in enumerate(records[:limit])):
        raise ValueError('Stitch-hint pointers require contiguous initial geometry')
    def pointer(token,nullable=False):
        value=token.get('value')
        if token.get('kind')!='pointer' or type(value) is not int:raise ValueError('Stitch-hint association lacks typed pointer')
        if nullable and value==-1:return None
        if not 0<=value<limit:raise ValueError('Stitch-hint pointer leaves initial geometry')
        return value
    def minus_one(token):
        if token.get('kind')!='integer' or type(token.get('value')) is not int or token['value']!=-1:
            raise ValueError('Stitch-hint common integer header differs')
    index=record.get('index')
    if (type(index) is not int or not 0<=index<limit or records[index]!=record
            or record.get('name')!=NAME or len(record.get('tokens',[]))!=8):
        raise ValueError('Unsupported stitch-hint record class/count/identity')
    tokens=record['tokens'];minus_one(tokens[1])
    if pointer(tokens[0],True) is not None or pointer(tokens[2],True) is not None:
        raise ValueError('Stitch-hint must be terminal with no attribute child')
    previous=pointer(tokens[3]);owner_id=pointer(tokens[4]);owner=records[owner_id]
    if owner['name']!='edge' or not owner['tokens'] or pointer(owner['tokens'][0])!=previous:
        raise ValueError('Stitch-hint owner is not EDGE with the claimed generic head')
    generic=records[previous];gt=generic['tokens']
    if (generic['name']!='ATTRIB_CUSTOM-attrib' or len(gt)<6 or gt[5].get('kind')!='string'
            or gt[5].get('value')!='generic_tag_attrib_def'):
        raise ValueError('Stitch-hint previous sibling is not a generic naming attribute')
    minus_one(gt[1])
    if (pointer(gt[0],True) is not None or pointer(gt[3],True) is not None
            or pointer(gt[2])!=index or pointer(gt[4])!=owner_id):
        raise ValueError('Stitch-hint generic head/next/previous/owner links do not reciprocate')
    values=[]
    for token in tokens[5:]:
        value=token.get('value')
        if token.get('kind')!='double' or type(value) is not float or not math.isfinite(value):
            raise ValueError('Stitch-hint requires three finite typed double payload fields')
        values.append(value)
    offsets=[t['offset'] for t in tokens]
    if (offsets[0]!=record['offset']+len(NAME_BYTES) or offsets!=list(range(offsets[0],offsets[0]+72,9))
            or record['end_offset']!=offsets[-1]+10):
        raise ValueError('Stitch-hint exact token byte extents disagree')
    fields=b''.join(bytes([12 if t['kind']=='pointer' else 4])+struct.pack('<q',t['value']) for t in tokens[:5])
    numeric=b''.join(b'\x06'+struct.pack('<d',value) for value in values);fields+=numeric
    return {'attribute_record_index':index,'attribute_class_name':NAME,'owner_record_index':owner_id,'owner_kind':'edge',
        'owner_attribute_chain':[previous,index],'previous_attribute_record_index':previous,'next_attribute_record_index':None,
        'stored_child_pointer':-1,'stored_integer_header':-1,'stored_terminal_next_pointer':-1,
        'stored_payload_doubles':values,'payload_scope':'Three literal finite double fields; no tolerance, distance, direction, solver or selected topology meaning assigned',
        'typed_token_offsets':offsets,'record_offset':record['offset'],'record_end_offset':record['end_offset'],
        'numeric_payload_offset':offsets[5],'numeric_payload_end_offset':offsets[-1]+9,'numeric_payload_hex':numeric.hex(),
        'record_fields_offset':offsets[0],'record_fields_end_offset':offsets[-1]+9,'record_fields_hex':fields.hex(),
        'record_hex':(NAME_BYTES+fields+b'\x11').hex(),
        'offset_scope':'Absolute bytes in original same-blob ASM buffer; no coordinate normalization or historical pointer conversion',
        'association':'Exact reciprocal EDGE attribute-head→generic-tag→terminal stitch-hint next/previous/owner references'}
