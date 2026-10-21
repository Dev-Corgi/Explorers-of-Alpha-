/* Standalone overlay36 payload installed after mega_evolve. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed short s16;
#define FN(a,t) ((t)(a))
#define U16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define U32(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define BYTE(p,o) (*((u8 *)(p)+(o)))
static u8 *dungeon(void) {return *(u8 **)0x02353538;}
static u8 *monster(u8 *e) {return e && U32(e,0)==1?(u8 *)U32(e,0xb4):0;}
static int clamp(int x,int lo,int hi) {return x<lo?lo:x>hi?hi:x;}
#include "tower_core.c"

void ME_TowerQuickSave(u8 *out) {ME_TowerSave(out);}
int ME_TowerQuickLoad(const u8 *in) {return ME_TowerLoad(in);}
void ME_TowerQuickReady(const u8 *in) {ME_TowerLoad(in);}
void ME_TowerSpringComplete(void) {
    if(!FN(0x0204CF9C,int(*)(int))(TT_DUNGEON))
        FN(0x0204D018,void(*)(int,int))(TT_DUNGEON,1);
    FN(0x0204B988,void(*)(int,int,int,int))(0,0x53,TT_DUNGEON,1);
    FN(0x0204B988,void(*)(int,int,int,int))(0,0x55,TT_DUNGEON+1,1);
}
