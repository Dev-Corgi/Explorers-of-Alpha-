/* Additional cache slots are heap BSS, never the native1155-slot array. */
#include "phase5_decode.c"
static s16 form_sprite_cache[ME_FORM_COUNT];
static u32 form_sprite_dungeon;
static u16 form_sprite_owners[ME_FORM_COUNT];
static u32 form_sprite_md;
static int sprite_owner(int species) {
    if(!ME_FindForm(species))return species;
    u8 *md=*(u8**)0x020B09B4;
    if(form_sprite_md!=(u32)md){zero(form_sprite_owners,sizeof(form_sprite_owners));form_sprite_md=(u32)md;}
    int cached=form_sprite_owners[species-ME_FORM_FIRST];if(cached)return cached;
    u16 sprite=U16(md,species*68+16);
    for(int i=ME_FORM_FIRST;i<ME_FORM_FIRST+ME_FORM_COUNT;i++)
        if(U16(md,i*68+16)==sprite){form_sprite_owners[species-ME_FORM_FIRST]=i;return i;}
    return species;
}
int ME_SpriteCacheGet(int species) {
    u8 *d=dungeon();if(!d)return 0;
    if(form_sprite_dungeon!=(u32)d){zero(form_sprite_cache,sizeof(form_sprite_cache));form_sprite_dungeon=(u32)d;}
    species=sprite_owner(species);
    if(species>=ME_FORM_FIRST && species<ME_FORM_FIRST+ME_FORM_COUNT)
        return form_sprite_cache[species-ME_FORM_FIRST];
    return species>=0 && species<ME_FORM_FIRST?(s16)U16(d,0x19914+species*2):0;
}
void ME_SpriteCacheSet(int species,int index) {
    ME_SpriteCacheGet(species);species=sprite_owner(species);
    if(species>=ME_FORM_FIRST && species<ME_FORM_FIRST+ME_FORM_COUNT)
        form_sprite_cache[species-ME_FORM_FIRST]=index;
    else if(dungeon() && species>=0 && species<ME_FORM_FIRST)U16(dungeon(),0x19914+species*2)=index;
}
void ME_SpriteCacheDelete(int species) {
    int index=ME_SpriteCacheGet(species);if(!index)return;
    FN(0x0201d72c,void(*)(void*,int))(*(void**)0x020AFC68,index);
    ME_SpriteCacheSet(species,0);
}
void ME_SpriteCacheSwap(int source,int target) {
    if(sprite_owner(source)==sprite_owner(target))return;
    int index=ME_SpriteCacheGet(source);if(!index)return;
    int sprite=FN(0x020526ec,int(*)(int))(target);
    if(!FN(0x0201d684,int(*)(void*,int,int,int,int))(*(void**)0x020AFC68,index,0,sprite,1))return;
    ME_SpriteCacheSet(target,index);ME_SpriteCacheSet(source,0);
}
static u8 *read_sprite(int pack,int index,int flags,int *out_length) {
    int size=FN(0x0200c33c,int(*)(int,int))(pack,index);
    if(size<12 || size>0x200000)return 0;
    u8 *packed=FN(0x02001170,u8*(*)(int,int))(size,flags);
    if(!packed)return 0;
    FN(0x0200c35c,void(*)(int,int,u8*))(pack,index,packed);
    int direct=U32(packed,0)==0x30524953;
    int length=direct?size:FN(0x020204ec,int(*)(u8*))(packed);
    u8 *raw=0;
    if(length>0 && length<=0x200000)
        raw=FN(0x02001170,u8*(*)(int,int))(length,flags);
    if(!raw){FN(0x02001188,void(*)(void*))(packed);return 0;}
    int decoded=length;
    if(direct){for(int i=0;i<length;i++)raw[i]=packed[i];}
    else decoded=FN(0x0201f5c0,int(*)(u8*,int,u8*))(raw,length,packed);
    FN(0x02001188,void(*)(void*))(packed);
    if(decoded!=length){FN(0x02001188,void(*)(void*))(raw);return 0;}
    *out_length=length;return raw;
}
int ME_LoadNewSprite(u8 *manager,int pack,int index,int flags,int compressed) {
    (void)compressed;
    int slot=FN(0x0201d334,int(*)(u8*,int,int,int))(manager,pack,index,flags);
    if(slot>=0){U16(manager,slot*56+0x2c)++;return slot;}
    int length=0;u8 *raw=read_sprite(pack,index,flags,&length);
    if(!raw)return -1;
    slot=FN(0x0201d244,int(*)(u8*))(manager);
    if(slot<0){FN(0x02001188,void(*)(void*))(raw);return -1;}
    u8 *row=manager+slot*56;
    BYTE(row,0x20)=0;
    BYTE(row,0x21)=2;U16(row,0x22)=pack;U16(row,0x24)=index;
    U32(row,0x28)=length;U16(row,0x2c)++;U32(row,0x34)=(u32)raw;
    FN(0x0201f58c,void(*)(u8*,u8*))(row+0x30,raw);
    return slot;
}
int ME_ReplaceNewSprite(u8 *manager,int slot,int pack,int index,int compressed) {
    (void)compressed;
    int length=0;u8 *raw=read_sprite(pack,index,0,&length);if(!raw)return 0;
    u8 *row=manager+slot*56,*old=(u8*)U32(row,0x34);int borrowed=BYTE(row,0x20);
    BYTE(row,0x20)=0;
    BYTE(row,0x21)=2;U16(row,0x22)=pack;U16(row,0x24)=index;
    U32(row,0x28)=length;U32(row,0x34)=(u32)raw;
    FN(0x0201f58c,void(*)(u8*,u8*))(row+0x30,raw);
    if(old && !borrowed)FN(0x02001188,void(*)(void*))(old);
    return 1;
}
