import collections,hashlib,json,lzma,runpy,zipfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
GRAPH=runpy.run_path(str(BASE.parent/'EntityGraph/DecodeGraph.py'))
SCHEMA=ROOT/'re/Fusion/LocalOracle/TSplineReflection/Versions.json'
GRAPH['GraphCodec'].__init__.__globals__['SCHEMA_PATH']=SCHEMA


def main():
 rows=[]
 for path in sorted((ROOT/'re/Fusion/LocalOracle/TSpline').glob('*.f3d')):
  graph=GRAPH['inspect'](path)
  selected=[record for record in graph['records'] if 'tspline' in record['class'].lower()]
  with zipfile.ZipFile(path) as archive:
   names=archive.namelist();members=[]
   for name in names:
    if name.endswith('.tsm') or '/OGS/' in name and not name.endswith('/'):
     raw=archive.read(name);members.append({'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
  rows.append({'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'records':len(graph['records']),'status_counts':graph['statusCounts'],'unresolved':[{'identity':r['entityId'],'class':r['class'],'version':r['schemaVersion'],'error':r.get('error')} for r in graph['records'] if r['status']!='reencoded'],'tspline_records':selected,'members':members})
 encoded=lzma.compress(json.dumps(rows,indent=2).encode());(BASE/'DocumentLinks.json.xz').write_bytes(encoded)
 summary={'scope':'Read-only raw archive and independently decoded entity graph; no production execution or native calls','reflection':str(SCHEMA.relative_to(ROOT)),'reflection_sha256':hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),'details':'DocumentLinks.json.xz','sha256':hashlib.sha256(encoded).hexdigest(),'sources':[]}
 for row in rows:
  counts=collections.Counter((r['class'],r['version'],r['error']) for r in row['unresolved'])
  summary['sources'].append({'source':row['source'],'records':row['records'],'status_counts':row['status_counts'],'unresolved_classes':[{'class':k[0],'version':k[1],'error':k[2],'records':count} for k,count in sorted(counts.items())],'members':row['members']})
 (BASE/'DocumentLinks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'sources':len(rows),'classes':sorted({r['class']+' v'+str(r['version']) for row in rows for r in row['unresolved']})}))

if __name__=='__main__':main()
