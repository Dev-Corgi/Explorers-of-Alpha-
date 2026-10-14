"""Cached SpriteCollab->WAN conversion. Source packages are read-only."""
from __future__ import annotations
import concurrent.futures,hashlib,json,math,struct,sys,time
from pathlib import Path
from .phase5 import MODULE,REPO,package
CACHE=MODULE/'.cache/phase5'

def deduplicate_pixels(wan):
    # ImportSheets deduplicates RGBA frames before palette conversion, but
    # repeating sprite pieces remain after chopping. Share identical packed
    # pixels losslessly; frame positions/timing/directions stay untouched.
    indices={};mapping={};pieces=[]
    for i,piece in enumerate(wan.imgData):
        key=(piece.zSort,tuple(bytes(strip) for strip in piece.imgPx))
        if key not in indices:indices[key]=len(pieces);pieces.append(piece)
        mapping[i]=indices[key]
    for frame in wan.frameData:
        for piece in frame:
            if piece.imgIndex>=0:piece.imgIndex=mapping[piece.imgIndex]
    wan.imgData=pieces

def convert(asset):
    from skytemple_files.graphics.chara_wan.handler import CharaWanHandler as Wan
    from skytemple_rust.st_pkdpx import Pkdpx
    directory=CACHE/asset['sha256'];marker=directory/'conversion.json'
    try:
        if marker.is_file():
            saved=json.loads(marker.read_text(encoding='utf-8'))
            if saved.get('pipeline')==3 and all(hashlib.sha256((directory/p).read_bytes()).hexdigest()==h for p,h in saved['outputs'].items()):return dict(saved,asset=asset['index'])
        path=REPO/asset['path']
        if package(path)['sha256']!=asset['sha256']:raise ValueError('source sprite changed since inventory')
        # SkyTemple's importer maps whole-package colors to the native16-color
        # palette, preserving transparent index0; no source PNG is rewritten.
        wan=Wan.import_sheets(str(path),strict=False)
        deduplicate_pixels(wan)
        if not wan.animGroupData[0] or not wan.animGroupData[7]:raise ValueError('Walk/Idle animation missing')
        directory.mkdir(parents=True,exist_ok=True);outputs={};sizes={};raw_sizes={}
        blocks=0;pages=0
        for name,part in zip(('monster','ground','attack'),Wan.split_wan(wan)):
            raw=bytes(Wan.serialize(part))
            if not part.frameData:raise ValueError(name+' has no frames')
            blob=raw
            if name!='ground':
                chunks=[Pkdpx.compress(raw[i:i+32768]).to_bytes() for i in range(0,len(raw),32768)]
                blob=struct.pack('<3I',0x3557454D,len(raw),len(chunks))
                blob+=b''.join(struct.pack('<I',len(c))+c+b'\0'*((-len(c))%4) for c in chunks)
                if b''.join(Pkdpx(c).decompress() for c in chunks)!=raw:raise ValueError('chunked sprite roundtrip failed')
            reread=Wan.deserialize(raw)
            if reread.get_filled_anims()!=part.get_filled_anims():raise ValueError('WAN animation roundtrip failed')
            blocks=max(blocks,part.get_max_blocks());pages=math.ceil(len(raw)/512) if name=='monster' else pages
            (directory/(name+'.wan')).write_bytes(blob)
            outputs[name+'.wan']=hashlib.sha256(blob).hexdigest();sizes[name]=len(blob);raw_sizes[name]=len(raw)
        if blocks>255:raise ValueError(f'native tile metadata byte limit: {blocks}')
        saved=dict(pipeline=3,asset=asset['index'],path=asset['path'],source_sha256=asset['sha256'],status='converted',
                   outputs=outputs,sizes=sizes,raw_sizes=raw_sizes,tile_slots=max(6,blocks),file_pages=pages,
                   palette_policy='SkyTemple import16; transparent index0',
                   cache=directory.relative_to(MODULE).as_posix())
        marker.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return saved
    except Exception as error:return dict(asset=asset['index'],path=asset['path'],status='failed',error=str(error))

def pack_ground(row):
    from patch_engine.mega_evolve_phase5_data import chunks
    directory=MODULE/row['cache'];marker=directory/'ground_pack.json';output=directory/'ground.mew5'
    if marker.is_file() and output.is_file():
        saved=json.loads(marker.read_text(encoding='utf-8'))
        if saved['raw_sha256']==row['outputs']['ground.wan'] and hashlib.sha256(output.read_bytes()).hexdigest()==saved['sha256']:return saved
    raw=(directory/'ground.wan').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=row['outputs']['ground.wan']:raise ValueError('ground cache drift')
    if len(raw)>0x200000:raise ValueError('ground WAN exceeds explicit2MiB resource limit')
    blob=chunks(raw);output.write_bytes(blob)
    saved=dict(raw_sha256=row['outputs']['ground.wan'],sha256=hashlib.sha256(blob).hexdigest(),size=len(blob))
    marker.write_text(json.dumps(saved,indent=2)+'\n',encoding='utf-8');return saved

def main():
    if '--ground-only' in sys.argv:
        rows=[json.loads(p.read_text(encoding='utf-8')) for p in CACHE.glob('*/conversion.json')]
        rows=[r for r in rows if r.get('pipeline')==3]
        with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
            result=list(pool.map(pack_ground,rows))
        print('packed ground',len(result),'bytes',sum(r['size'] for r in result));return
    inventory=json.loads((MODULE/'data/phase5_assets.json').read_text(encoding='utf-8'))
    results=[];started=time.monotonic();jobs=inventory['assets']
    if '--retry-failed' in sys.argv:
        previous=json.loads((MODULE/'data/phase5_conversion.json').read_text(encoding='utf-8'))
        results=[r for r in previous['assets'] if r['status']=='converted']
        ready={r['asset'] for r in results};jobs=[a for a in jobs if a['index'] not in ready]
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(convert,a) for a in jobs]
        for future in concurrent.futures.as_completed(futures):
            row=future.result();results.append(row)
            if row['status']=='failed':print('FAIL',row['path'],row['error'],flush=True)
            if len(results)%25==0:print(f"converted {len(results)}/{len(futures)} ({int(time.monotonic()-started)}s)",flush=True)
    results.sort(key=lambda r:r['asset'])
    report=dict(schema=1,converted=sum(r['status']=='converted' for r in results),total=len(results),
                total_bytes=sum(sum(r.get('sizes',{}).values()) for r in results),assets=results)
    (MODULE/'data/phase5_conversion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('conversion summary',report['converted'],report['total'],report['total_bytes'],flush=True)
    if report['converted']!=report['total']:raise SystemExit(1)
if __name__=='__main__':main()
