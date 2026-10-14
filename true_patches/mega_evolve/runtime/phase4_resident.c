#include "phase4_resident_generated.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct {u16 species,origin,parent,mega,shiny,stage,stats[6],ability[3],grade;} Form;
static const Form *find(int species) {
    if(species<FIRST || species>=TOTAL)return 0;
    u8 *md=*(u8 **)0x020B09B4;
    if(!md || *(u32 *)(md-4)!=TOTAL)return 0;
    u32 *tail=(u32 *)(md+TOTAL*68);
    if(tail[0]!=0x3446454D || tail[1]!=1 || tail[2]!=FIRST || tail[3]!=TOTAL-FIRST)return 0;
    const Form *f=(const Form *)(tail+4)+(species-FIRST);
    return f->species==species?f:0;
}
int ME_ResidentOrigin(int species) {
    const Form *f=find(species);
    if(!f)return species;
    if(!f->stage)return f->parent;
    const Form *root=find(f->origin);
    return root && !root->stage?root->parent:f->origin;
}
int ME_ResidentValid(int species) {
    if(species<FIRST)return -1;
    return find(species)!=0;
}
int ME_ResidentAsset(int species) {
    const Form *f=find(species);
    if(!f)return species;
    u8 *md=*(u8 **)0x020B09B4;
    u16 sprite=*(u16 *)(md+species*68+16);
#ifdef PHASE5
    for(int i=FIRST;i<TOTAL;i++)if(*(u16 *)(md+i*68+16)==sprite)return i;
    return species;
#else
    int origin=ME_ResidentOrigin(species);
    if(*(u16 *)(md+origin*68+16)==sprite)return origin;
    u16 dex=*(u16 *)(md+species*68+4);
    for(int i=1;i<FIRST;i++)if(*(u16 *)(md+i*68+16)==sprite && *(u16 *)(md+i*68+4)==dex)return i;
    return origin;
#endif
}
void ME_SwapAsset(int source,int target) {
    int a=ME_ResidentAsset(source),b=ME_ResidentAsset(target);
    if(source!=target && a==b)return;
    ((void (*)(int,int))SWAP_TRAMPOLINE)(a,b);
}
#ifdef PHASE5
#define RESIDENT_METADATA_ONLY 1
#include "phase5_decode.c"
#endif
