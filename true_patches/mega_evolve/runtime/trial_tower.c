/* Included in the relocatable dungeon payload. Only this dungeon's newly
 * allocated rooms are eligible; original bosses and their shared rows stay intact. */
#include "trial_tower_generated.h"
static u8 tt_order[9];
static int tt_valid;
void ME_TowerReset(void) { tt_valid=0; }
void ME_TowerSave(u8 *out) {
    U32(out,0)=tt_valid?0x3154544d:0;
    for(int i=0;i<9;i++)out[4+i]=tt_order[i];
}
int ME_TowerLoad(const u8 *in) {
    if(!U32(in,0)) {tt_valid=0;return 1;}
    if(U32(in,0)!=0x3154544d)return 0;
    int mask=0;
    for(int i=0;i<9;i++) {
        if(in[4+i]>=9 || (mask&(1<<in[4+i])))return 0;
        mask|=1<<in[4+i];
    }
    for(int i=0;i<9;i++)tt_order[i]=in[4+i];
    tt_valid=1;return 1;
}
static int tt_room(void) {
    u8 *d=dungeon();
    if(!d || BYTE(d,0x748)!=TT_DUNGEON)return -1;
    int room=BYTE(d,0x40da)-TT_ROOM_FIRST;
    return room>=0 && room<10?room:-1;
}
static void tt_shuffle(void) {
    if(tt_valid)return;
    for(int i=0;i<9;i++)tt_order[i]=(u8)i;
    for(int i=8;i>0;i--) {
        int j=FN(0x022eaa98,int(*)(int))(i+1);
        u8 t=tt_order[i];tt_order[i]=tt_order[j];tt_order[j]=t;
    }
    tt_valid=1;
}
/* Fixed-room sprite preloading must choose the same species as actual spawn. */
int ME_TowerSpecies(int species) {
    int room=tt_room();if(room<0)return species;
    tt_shuffle();
    if(room<9 && species==415)return tt_bosses[tt_order[room]].species;
    if(room==9 && species==549)return tt_final[0].species;
    return species;
}
/* Native Alpha selector runs first, then our dedicated rooms override only
 * species/level on the spawn descriptor, before ability/sprite/move setup. */
void ME_TowerSpawn(u8 *spawn) {
    int room=tt_room();if(room<0 || BYTE(spawn,2)!=6)return;
    tt_shuffle();
    if(room<9) {U16(spawn,0)=tt_bosses[tt_order[room]].species;U16(spawn,8)=tt_levels[room];}
    else {
        for(int i=0;i<3;i++)if(U16(spawn,0)==(i==0?549:tt_final[i].species)) {
            U16(spawn,0)=tt_final[i].species;U16(spawn,8)=60;break;
        }
    }
}
/* Called after the existing Strong Enemy table application and V cleanup. */
void ME_TowerStats(u8 *e) {
    int room=tt_room();u8 *m=monster(e);if(room<0 || !m)return;
    int species=U16(m,2),level=room<9?tt_levels[room]:60;
    const TTBoss *boss=0;
    if(room<9) {tt_shuffle();boss=&tt_bosses[tt_order[room]];}
    else for(int i=0;i<3;i++)if(species==tt_final[i].species)boss=&tt_final[i];
    if(!boss || species!=boss->species)return;
    BYTE(m,0xa)=(u8)level;
    int hp=FN(FORM_STAT_RESUME,int(*)(int,int,int,int))(species,level,0,0);
    hp=clamp(hp*(room<9?4:2),1,32767);U16(m,0x10)=U16(m,0x12)=(u16)hp;
    U16(m,0xe)=999;
    FN(0x02301fbc,void(*)(u8*))(m);
    /* Initialize real move structs, including native PP and AI enable flags. */
    for(int i=0;i<4;i++) {
        u8 *move=m+0x124+i*8;
        FN(0x020137b8,void(*)(u8*,int))(move,boss->moves[i]);
    }
}
