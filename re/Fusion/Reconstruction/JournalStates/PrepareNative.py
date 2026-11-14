import argparse
import hashlib
import json
import lzma
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from EmitJournal import emit_journal


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[4]
    semantic=Path(__file__).with_name('SemanticHistory.json.xz')
    models=json.loads(lzma.decompress(semantic.read_bytes()))
    args.output.mkdir(parents=True,exist_ok=True)
    results=[]
    for model in models:
        if len(model['states'])!=3:continue
        source=root/model['source']['path']
        label='Draft' if source.stem=='Draft' else 'OffsetCylinder'
        target=args.output/(label+'TypedHistory.f3d')
        emitted=emit_journal(model)
        geometry=args.output/(label+'TypedHistory.smbh')
        geometry.write_bytes(emitted)
        with ZipFile(source) as original,ZipFile(target,'w',compression=ZIP_DEFLATED) as output:
            replaced=False
            for entry in original.infolist():
                data=original.read(entry.filename)
                if entry.filename==model['source']['member']:
                    if hashlib.sha256(data).hexdigest()!=model['source']['sha256']:raise ValueError('Source history changed')
                    source_match=data==emitted
                    data=emitted;replaced=True
                output.writestr(entry.filename,data)
            if not replaced:raise ValueError('Missing source history member')
        results.append(dict(source=str(source),sourceArchiveSha256=hashlib.sha256(source.read_bytes()).hexdigest(),target=str(target),targetArchiveSha256=hashlib.sha256(target.read_bytes()).hexdigest(),history=str(geometry),sourceHistorySha256=model['source']['sha256'],emittedHistorySha256=hashlib.sha256(emitted).hexdigest(),bytes=len(emitted),sourceHistoryByteIdentical=source_match,activeCount=model['activeCount'],archivedCount=len(model['entities'])-model['activeCount'],states=[{'stateId':state['stateId'],'entityCount':state['entityCount'],'carriers':state['carriers']} for state in model['snapshots']],scope='Complete geometry/history member authored from named semantic fields; each archive retains its own other original members; no independent Design authoring claim'))
    report={'schema':'FusionSemanticJournalNativePreparation/1','semanticEvidence':str(semantic),'semanticEvidenceSha256':hashlib.sha256(semantic.read_bytes()).hexdigest(),'nativeAcceptance':'pending','productionRuntime':False,'sources':results}
    (args.output/'Preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:value for key,value in report.items() if key!='sources'},indent=2))
    for result in results:print(result['target'],result['emittedHistorySha256'],result['sourceHistoryByteIdentical'])

if __name__=='__main__':main()
