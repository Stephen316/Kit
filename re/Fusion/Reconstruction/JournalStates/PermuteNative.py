import copy
import hashlib
import json
import lzma
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from EmitJournal import emit_journal

base=Path(__file__).resolve().parent
root=base.parents[3]
out=root/'re/Fusion/LocalOracle/JournalStates'


def permute(model):
    result=copy.deepcopy(model)
    count=model['activeCount'];total=len(model['entities'])
    order=[0,*reversed(range(1,count)),*reversed(range(count,total))]
    mapping={old:new for new,old in enumerate(order)}
    entities=[]
    names={
        'asmheader':('attribute',),
        'body':('firstLump','firstWire','transform'),
        'lump':('nextLump','firstShell','ownerBody'),
        'shell':('nextShell','firstSubshell','firstFace','wire','ownerLump'),
        'face':('nextFace','firstLoop','ownerShell','reservedFaceRef','surface'),
        'loop':('nextLoop','firstCoedge','ownerFace'),
        'coedge':('nextCoedge','previousCoedge','partnerCoedge','edge','ownerLoop','pcurve'),
        'edge':('startVertex','endVertex','ownerCoedge','curve'),
        'vertex':('ownerEdge','point'),
        'ATTRIB_CUSTOM-attrib':('reserved','next','previous','owner'),
    }
    for index in order:
        record=copy.deepcopy(model['entities'][index]);kind=record['kind']
        refs=names.get(kind,())
        if kind not in ('asmheader','ATTRIB_CUSTOM-attrib'):refs+=('attribute','reservedRef')
        for key in refs:
            value=record['fields'][key]
            record['fields'][key]=mapping[value] if value>=0 else value
        entities.append(record)
    result['entities']=entities
    for state in result['states']:
        for board in state['boards']:
            for change in board['changes']:
                for key in ('old','new'):
                    if change[key]>=0:change[key]=mapping[change[key]]
    owner=result['stream']['ownerEntity']
    if owner>=0:result['stream']['ownerEntity']=mapping[owner]
    return result,mapping


def main():
    models=json.loads(lzma.decompress((base/'SemanticHistory.json.xz').read_bytes()))
    report=[]
    out.mkdir(parents=True,exist_ok=True)
    for model in models:
        if len(model['states'])!=3:continue
        changed,mapping=permute(model)
        emitted=emit_journal(changed)
        source=root/model['source']['path']
        label='Draft' if source.stem=='Draft' else 'OffsetCylinder'
        target=out/(label+'PermutedHistory.f3d')
        geometry=out/(label+'PermutedHistory.smbh')
        geometry.write_bytes(emitted)
        with ZipFile(source) as original,ZipFile(target,'w',compression=ZIP_DEFLATED) as archive:
            for entry in original.infolist():
                value=emitted if entry.filename==model['source']['member'] else original.read(entry.filename)
                archive.writestr(entry.filename,value)
        report.append(dict(source=str(source),sourceArchiveSha256=hashlib.sha256(source.read_bytes()).hexdigest(),target=str(target),targetArchiveSha256=hashlib.sha256(target.read_bytes()).hexdigest(),history=str(geometry),historySha256=hashlib.sha256(emitted).hexdigest(),sourceHistorySha256=model['source']['sha256'],sourceHistoryByteIdentical=hashlib.sha256(emitted).hexdigest()==model['source']['sha256'],entityPermutation=mapping,stateNodeIdentitiesUnchanged=changed['states']==[{**state,'boards':changed['states'][index]['boards']} for index,state in enumerate(model['states'])],semanticIdentityFields='Body entityTag, generic tag IDs/operations, trackedTagId, sketch IDs, stream state IDs and nextEntityTag remain unchanged',activeCount=model['activeCount'],archivedCount=len(model['entities'])-model['activeCount']))
    (out/'PermutationPreparation.json').write_text(json.dumps({'schema':'FusionSemanticJournalPermutation/1','scope':'Authorized native-acceptance artifacts; explicit semantic entity allocation permutation without Design identity changes; no local tests or native calls','nativeAcceptance':'pending','sources':report},indent=2)+'\n')
    for result in report:print(result['target'],result['historySha256'])

if __name__=='__main__':main()
