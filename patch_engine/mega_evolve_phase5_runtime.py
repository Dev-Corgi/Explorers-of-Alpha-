"""Guarded native cache extensions; existing arrays stay in place."""
import struct
from .mega_evolve_runtime import branch,word
from .state import HookRecord

def install(rom,symbols,resident,record,total):
    overlay=rom.loadArm9Overlays()[29];base=overlay.ramAddress;edits=[]
    replacements=[(0x022F7388,branch(0x022F7388,resident['ME_SpriteCacheIndex']),'ME_SpriteCacheGet',False),
                  (0x022F740C,0xE92D40F8,'ME_SpriteCacheStoreHook',False),
                  (0x022F74F0,0xE19210F1,'ME_SpriteCacheReadHook',True),
                  (0x022FBB6C,0xE19110FA,'ME_SpriteActorCacheReadHook',True),
                  (0x022F7768,0xE92D4038,'ME_SpriteCacheDeleteHook',False),
                  (0x022F75D4,branch(0x022F75D4,resident['ME_SwapAsset']),'ME_SpriteCacheSwapHook',False)]
    for site,prior,name,link in replacements:
        if word(overlay.data,site,base)!=prior:raise RuntimeError(f'phase5 sprite cache guard {site:#x}')
        value=branch(site,symbols[name],link);struct.pack_into('<I',overlay.data,site-base,value)
        edits.append(dict(site=site,before=prior,after=value))
        record.hooks.append(HookRecord(name,site,'bl' if link else 'b',name,'expanded_sprite_cache'))
    site=0x022F7830
    if word(overlay.data,site,base)!=1155:raise RuntimeError('phase5 sprite delete loop bound changed')
    struct.pack_into('<I',overlay.data,site-base,total);edits.append(dict(site=site,before=1155,after=total))
    rom.files[overlay.fileID]=bytes(overlay.data)
    return edits

def verify(rom,edits):
    ov=rom.loadArm9Overlays()[29]
    for e in edits:
        if word(ov.data,e['site'],ov.ramAddress)!=e['after']:raise AssertionError('phase5 cache hook changed')
