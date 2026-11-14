import math
import struct


def integer(value, tag=4):
    if type(value) is not int or not -(1<<63)<=value<1<<63:raise ValueError('Invalid signed wire integer')
    return bytes((tag,))+struct.pack('<q',value)


def number(value):
    if type(value) not in (float,int) or not math.isfinite(value):raise ValueError('Invalid finite scalar')
    return b'\x06'+struct.pack('<d',value)


def text(value,tag=7):
    payload=value.encode('ascii')
    if b'\0' in payload or len(payload)>255:raise ValueError('Invalid qualified ASCII text')
    return bytes((tag,len(payload)))+payload


def name(value):
    parts=value.split('-')
    return b''.join(text(part,13 if index==len(parts)-1 else 14) for index,part in enumerate(parts))


class Values:
    def __init__(self,fields):self.fields=dict(fields);self.output=bytearray()
    def take(self,key,tag):
        value=self.fields.pop(key)
        if tag in (4,12):encoded=integer(value,tag)
        elif tag==6:encoded=number(value)
        elif tag==7:encoded=text(value)
        elif tag in (19,20):
            if len(value)!=3 or any(not math.isfinite(item) for item in value):raise ValueError('Invalid vector')
            encoded=bytes((tag,))+struct.pack('<3d',*value)
        else:raise ValueError('Unknown declared field tag')
        self.output.extend(encoded)
        return value
    def boolean(self,key):
        value=self.fields.pop(key)
        if type(value) is not bool:raise ValueError('Invalid logical')
        self.output.append(10 if value else 11)
        return value
    def bound(self,key):
        value=self.fields.pop(key)
        self.output.extend(b'\x0b' if value is None else b'\x0a'+number(value))
    def done(self):
        if self.fields:raise ValueError('Unknown semantic fields '+str(tuple(self.fields)))
        return bytes(self.output)


def attribute(writer):
    for key,tag in (('reserved',12),('marker',4),('next',12),('previous',12),('owner',12)):
        writer.take(key,tag)
    family=writer.take('family',7)
    if family in ('Timestamp_attrib_def','FPM_tracked_attrib_def'):
        writer.output.extend(integer(1))
        writer.take('unixMicroseconds' if family=='Timestamp_attrib_def' else 'trackedTagId',6 if family=='Timestamp_attrib_def' else 4)
    elif family=='sketch_attrib_def':
        writer.output.extend(integer(1)+integer(1)+integer(3))
        link=writer.fields.pop('sourceLink')
        keys=('primaryId','secondaryId','direction','topologyRoleFlags','splitSequenceId','splitTotalNumber')
        if set(link)!=set(keys):raise ValueError('Invalid source-link fields')
        writer.output.extend(text(' '.join(str(link[key]) for key in keys)))
    elif family=='generic_tag_attrib_def':
        groups=writer.fields.pop('groups')
        writer.output.extend(integer(3)+integer(3)+integer(-1)+text(family+' ')+integer(len(groups)))
        for group in groups:
            if set(group)!={'primaryId','secondaryId','operationIds','approachId'}:raise ValueError('Invalid feature-tag fields')
            writer.output.extend(integer(len(group['primaryId'].encode('ascii')))+text(group['primaryId'])+integer(group['secondaryId'])+integer(len(group['operationIds'])))
            writer.output.extend(b''.join(integer(item) for item in group['operationIds']))
            writer.output.extend(integer(group['approachId']))
    else:raise ValueError('Unsupported attribute family')


def emit_entity(record):
    kind=record['kind'];writer=Values(record['fields'])
    if kind=='ATTRIB_CUSTOM-attrib':attribute(writer)
    else:
        writer.take('attribute',12);writer.take('entityTag',4)
        if kind=='asmheader':writer.take('kernelVersion',7)
        else:
            writer.take('reservedRef',12)
            links={'body':('firstLump','firstWire','transform'),'lump':('nextLump','firstShell','ownerBody'),'shell':('nextShell','firstSubshell','firstFace','wire','ownerLump'),'loop':('nextLoop','firstCoedge','ownerFace')}
            if kind in links:
                for key in links[kind]:writer.take(key,12)
            elif kind=='face':
                for key in ('nextFace','firstLoop','ownerShell','reservedFaceRef','surface'):writer.take(key,12)
                writer.boolean('reversed')
                if writer.boolean('doubleSided'):writer.boolean('contained')
                elif writer.fields.pop('contained') is not None:raise ValueError('Single-sided face containment must be absent')
            elif kind=='coedge':
                for key in ('nextCoedge','previousCoedge','partnerCoedge','edge'):writer.take(key,12)
                writer.boolean('reversed');writer.take('ownerLoop',12);writer.take('reservedInt',4);writer.take('pcurve',12)
            elif kind=='edge':
                for key,tag in (('startVertex',12),('startParameter',6),('endVertex',12),('endParameter',6),('ownerCoedge',12),('curve',12)):writer.take(key,tag)
                writer.boolean('reversed');writer.take('convexity',7)
            elif kind=='vertex':writer.take('ownerEdge',12);writer.take('edgeIndex',4);writer.take('point',12)
            elif kind=='point':writer.take('positionCm',19)
            elif kind=='plane-surface':
                writer.take('originCm',19);writer.take('normal',20);writer.take('referenceAxis',20);writer.boolean('reversedV')
                for key in ('uLower','uUpper','vLower','vUpper'):writer.bound(key)
            elif kind in ('cone-surface','ellipse-curve'):
                writer.take('originCm',19);writer.take('axis',20);writer.take('majorAxisCm',20);writer.take('ellipseRatio',6)
                writer.bound('ellipseLower');writer.bound('ellipseUpper')
                if kind=='cone-surface':
                    for key in ('sineAngle','cosineAngle','uScaleCm'):writer.take(key,6)
                    writer.boolean('reversed')
                    for key in ('uLower','uUpper','vLower','vUpper'):writer.bound(key)
            else:raise ValueError('Unsupported geometry kind')
    return name(kind)+writer.done()+b'\x11'
