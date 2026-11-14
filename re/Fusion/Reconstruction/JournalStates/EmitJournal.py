import struct

from EmitEntities import emit_entity, integer, name, number, text
from ValidateJournal import validate_journal


def emit_state(state):
    output=bytearray(name('delta_state'))
    for key,tag in (('stateId',4),('backward',4),('hidden',4),('previousNode',12),('nextNode',12),('partnerNode',12),('mergedWithNode',12),('ownerStream',12)):
        output.extend(integer(state[key],tag))
    output.extend(b'\x0b' if state['name'] is None else b'\x0a'+text(state['name']))
    for board in state['boards']:
        output.extend(integer(1)+integer(board['ownerNode'],12)+integer(board['status']))
        for change in board['changes']:
            if change['kind']!=('insert' if change['old']==-1 else 'delete' if change['new']==-1 else 'replace'):raise ValueError('Inconsistent change kind')
            output.extend(integer(1)+integer(change['old'],12)+integer(change['new'],12))
        output.extend(integer(0))
    output.extend(integer(0)+integer(len(state['stateList48'])))
    output.extend(b''.join(integer(item,12) for item in state['stateList48']))
    return bytes(output)+b'\x11'


def emit_journal(model):
    validate_journal(model)
    header=model['header']
    if header['saveFormat']!=23200 or header['storedRecords']!=0 or header['rootCount']!=2 or header['flags']!=3:raise ValueError('Unsupported embedded history header')
    output=bytearray(b'ASM BinaryFile8'+struct.pack('<4q',header['saveFormat'],header['storedRecords'],header['rootCount'],header['flags']))
    output.extend(b''.join(text(header[key]) for key in ('product','version','savedAt')))
    output.extend(b''.join(number(header[key]) for key in ('units','absoluteTolerance','normalTolerance')))
    count=model['activeCount']
    output.extend(b''.join(emit_entity(record) for record in model['entities'][:count]))
    stream=model['stream']
    output.extend(name('Begin-of-ASM-History-Data')+name('history_stream'))
    output.extend(b''.join(integer(stream[key]) for key in ('currentStateId','maxStateId','maxStatesToKeep','nextEntityTag')))
    output.extend(b''.join(integer(stream[key],12) for key in ('workingNode','activeNode','initialNode','ownerEntity')))
    output.extend(b'\x11')
    output.extend(b''.join(emit_state(state) for state in model['states']))
    output.extend(name('End-of-ASM-History-Section'))
    output.extend(b''.join(emit_entity(record) for record in model['entities'][count:]))
    output.extend(name('End-of-ASM-data'))
    return bytes(output)
