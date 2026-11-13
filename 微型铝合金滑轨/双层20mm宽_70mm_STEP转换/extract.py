import cadquery as cq,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent;p=next(root.glob('*.step'));s=cq.importers.importStep(str(p)).val();b=s.BoundingBox();d={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bbox_mm':[b.xlen,b.ylen,b.zlen],'valid':s.isValid(),'parts':[]}
for i,x in enumerate(s.Solids()):
 b=x.BoundingBox();v,f=x.tessellate(.025,.12);d['parts'].append({'name':f'STEP_Solid_{i+1}','vertices':[p.toTuple() for p in v],'faces':f,'bbox_mm':[b.xlen,b.ylen,b.zlen],'volume_mm3':x.Volume(),'valid':x.isValid()})
(root/'mesh.json').write_text(json.dumps(d));print({k:v for k,v in d.items() if k!='parts'});print([(x['name'],x['bbox_mm'],x['volume_mm3']) for x in d['parts']])
