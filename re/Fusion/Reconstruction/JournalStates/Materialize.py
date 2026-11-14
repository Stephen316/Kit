import collections
import hashlib
import json
import lzma
from pathlib import Path

base = Path(__file__).resolve().parent

class Fields:
    def __init__(self, record):
        self.values=record['fields'];self.position=0
    def take(self, tag):
        value=self.values[self.position];self.position+=1
        if value['tag']!=tag:raise ValueError(f'Expected {tag}, got {value}')
        return value['value']
    def boolean(self):
        value=self.values[self.position];self.position+=1
        if value['tag'] not in (10,11):raise ValueError('Expected logical')
        return value['tag']==10
    def bound(self):
        return self.take(6) if self.boolean() else None
    def done(self):
        if self.position!=len(self.values):raise ValueError('Trailing semantic fields')


def attribute(reader):
    result=dict(reserved=reader.take(12),marker=reader.take(4),next=reader.take(12),previous=reader.take(12),owner=reader.take(12),family=reader.take(7))
    if result['reserved']!=-1 or result['marker']!=-1:raise ValueError('Unsupported attribute prefix')
    family=result['family']
    if family=='Timestamp_attrib_def':
        if reader.take(4)!=1:raise ValueError('Unsupported timestamp schema')
        result['unixMicroseconds']=reader.take(6)
    elif family=='FPM_tracked_attrib_def':
        if reader.take(4)!=1:raise ValueError('Unsupported tracked schema')
        result['trackedTagId']=reader.take(4)
        if not -(1<<31)<=result['trackedTagId']<1<<31:raise ValueError('Invalid tracked tag')
    elif family=='sketch_attrib_def':
        if [reader.take(4) for _ in range(3)]!=[1,1,3]:raise ValueError('Unsupported sketch schema')
        fields=tuple(map(int,reader.take(7).split()))
        if len(fields)!=6:raise ValueError('Invalid sketch link')
        result['sourceLink']=dict(zip(('primaryId','secondaryId','direction','topologyRoleFlags','splitSequenceId','splitTotalNumber'),fields))
    elif family=='generic_tag_attrib_def':
        if [reader.take(4) for _ in range(3)]!=[3,3,-1] or reader.take(7)!=family+' ':raise ValueError('Unsupported generic tag schema')
        groups=[]
        for _ in range(reader.take(4)):
            size=reader.take(4);text=reader.take(7)
            if len(text.encode('ascii'))!=size:raise ValueError('Invalid primary length')
            secondary=reader.take(4);operations=tuple(reader.take(4) for _ in range(reader.take(4)));approach=reader.take(4)
            groups.append(dict(primaryId=text,secondaryId=secondary,operationIds=operations,approachId=approach))
        result['groups']=groups
    else:raise ValueError('Unsupported attribute family '+family)
    return result


def entity(record):
    reader=Fields(record);kind=record['name']
    if kind=='ATTRIB_CUSTOM-attrib':result=attribute(reader)
    else:
        result=dict(attribute=reader.take(12),entityTag=reader.take(4))
        if kind=='asmheader':result['kernelVersion']=reader.take(7)
        else:
            result['reservedRef']=reader.take(12)
            if result['reservedRef']!=-1:raise ValueError('Unsupported common pointer')
            links={
                'body':('firstLump','firstWire','transform'),
                'lump':('nextLump','firstShell','ownerBody'),
                'shell':('nextShell','firstSubshell','firstFace','wire','ownerLump'),
                'loop':('nextLoop','firstCoedge','ownerFace'),
            }
            if kind in links:result.update({name:reader.take(12) for name in links[kind]})
            elif kind=='face':
                result.update({name:reader.take(12) for name in ('nextFace','firstLoop','ownerShell','reservedFaceRef','surface')})
                result.update(reversed=reader.boolean(),doubleSided=reader.boolean())
                result['contained']=reader.boolean() if result['doubleSided'] else None
            elif kind=='coedge':
                result.update({name:reader.take(12) for name in ('nextCoedge','previousCoedge','partnerCoedge','edge')})
                result.update(reversed=reader.boolean(),ownerLoop=reader.take(12),reservedInt=reader.take(4),pcurve=reader.take(12))
            elif kind=='edge':
                result.update(startVertex=reader.take(12),startParameter=reader.take(6),endVertex=reader.take(12),endParameter=reader.take(6),ownerCoedge=reader.take(12),curve=reader.take(12),reversed=reader.boolean(),convexity=reader.take(7))
            elif kind=='vertex':result.update(ownerEdge=reader.take(12),edgeIndex=reader.take(4),point=reader.take(12))
            elif kind=='point':result['positionCm']=reader.take(19)
            elif kind=='plane-surface':
                result.update(originCm=reader.take(19),normal=reader.take(20),referenceAxis=reader.take(20),reversedV=reader.boolean())
                result.update({name:reader.bound() for name in ('uLower','uUpper','vLower','vUpper')})
            elif kind in ('cone-surface','ellipse-curve'):
                result.update(originCm=reader.take(19),axis=reader.take(20),majorAxisCm=reader.take(20),ellipseRatio=reader.take(6),ellipseLower=reader.bound(),ellipseUpper=reader.bound())
                if kind=='cone-surface':
                    result.update(sineAngle=reader.take(6),cosineAngle=reader.take(6),uScaleCm=reader.take(6),reversed=reader.boolean())
                    result.update({name:reader.bound() for name in ('uLower','uUpper','vLower','vUpper')})
            else:raise ValueError('Unsupported entity '+kind)
    reader.done()
    return dict(kind=kind,fields=result)


def materialize(entry,stream):
    count=entry['activeCount'];start=entry['archiveStartPhysical']
    records=stream['records'][:count]+[row for row in stream['records'][start:] if row['name']!='End-of-ASM-data']
    semantic=[entity(record) for record in records]
    aliases={index:index for index in range(len(records))}
    for state in entry['states']:
        for board in state['boards']:
            for change in board['changes']:
                if change['kind']=='replace':aliases[change['old']]=change['new']
    def stable(index):
        visited=set()
        while aliases[index]!=index:
            if index in visited:raise ValueError('Revision alias cycle')
            visited.add(index);index=aliases[index]
        return index
    versions={index:index for index in range(count)}
    selected=next(index for index,state in enumerate(entry['states']) if state['previousNode']==-1)
    seen=set();snapshots=[]
    while selected!=-1:
        if selected in seen:raise ValueError('State chain cycle')
        seen.add(selected);state=entry['states'][selected]
        issues=[]
        for slot,revision in versions.items():
            for field in records[revision]['fields']:
                if field['tag']==12 and field['value']>=0 and stable(field['value']) not in versions:
                    issues.append(dict(slot=slot,revision=revision,missingReference=field['value'],stableReference=stable(field['value'])))
        snapshot=dict(stateId=state['stateId'],node=selected,entityCount=len(versions),versions=dict(sorted(versions.items())),referenceIssues=issues,kinds=dict(collections.Counter(records[revision]['name'] for revision in versions.values())))
        snapshot['carriers']=[dict(slot=slot,revision=revision,**semantic[revision]) for slot,revision in versions.items() if records[revision]['name'] in ('cone-surface','ellipse-curve')]
        snapshots.append(snapshot)
        for board in state['boards']:
            for change in board['changes']:
                old,new=change['old'],change['new']
                if change['kind']=='insert':
                    if new not in versions:raise ValueError('Missing insertion target')
                    del versions[new]
                elif change['kind']=='delete':
                    if old in versions or old<count:raise ValueError('Invalid deletion revision')
                    versions[old]=old
                else:
                    if new not in versions or old<count:raise ValueError('Invalid replacement revision')
                    versions[new]=old
        selected=state['nextNode']
    if versions!={0:0} or len(seen)!=len(entry['states']):raise ValueError('History does not end at initial ASM header')
    header=stream['header']; tagged=[item['value'] for item in header['tagged_values']]
    header_model=dict(zip(('product','version','savedAt','units','absoluteTolerance','normalTolerance'),tagged))
    header_model.update(saveFormat=header['save_format'],storedRecords=header['stored_records'],rootCount=header['top_level_entity_count'],flags=header['flags'])
    stream_model=dict(zip(('currentStateId','maxStateId','maxStatesToKeep','nextEntityTag','workingNode','activeNode','initialNode','ownerEntity'),entry['preamble']))
    return dict(source=entry['sources'][0],header=header_model,stream=stream_model,activeCount=count,states=entry['states'],entities=semantic,revisionAliases={index:stable(index) for index in range(len(records))},snapshots=snapshots)


def main():
    inventory=json.loads(lzma.decompress((base/'Inventory.json.xz').read_bytes()))
    extended=json.loads(lzma.decompress((base/'ExtendedTokens.json.xz').read_bytes()))
    reports=[]
    for entry in inventory['entries']:
        digest=entry['sources'][0]['sha256']
        if digest not in extended:continue
        reports.append(materialize(entry,extended[digest]))
    encoded=lzma.compress(json.dumps(reports,indent=2).encode())
    (base/'SemanticHistory.json.xz').write_bytes(encoded)
    summary={'schema':'FusionMaterializedJournalSemantics/1','scope':'Read-only research semantic record decoding and explicit revision/reference graph reconstruction; no writer or vendor acceptance claim','evidence':'SemanticHistory.json.xz','sha256':hashlib.sha256(encoded).hexdigest(),'sources':[dict(source=report['source'],states=[{key:value for key,value in state.items() if key not in ('versions','carriers')} for state in report['snapshots']]) for report in reports]}
    (base/'Materialization.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
