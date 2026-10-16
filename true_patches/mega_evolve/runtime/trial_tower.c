/* Included in the relocatable dungeon payload. Only this dungeon's newly
 * allocated rooms are eligible; original bosses and their shared rows stay intact. */
#include "trial_tower_generated.h"
static u8 tt_order[9];
static int tt_valid;
static int tt_reward_pending,tt_reward_x,tt_reward_y;
static int tt_extended;
static void tt_restore_properties(const u8 *p) {
    u8 *native=(u8*)0x022c6c70+TT_KEY_ALIAS*12;
    for(int i=0;i<12;i++)native[i]=p[i];
}
void ME_TowerReset(void) { tt_valid=0;tt_reward_pending=0;tt_extended=0; }
void ME_TowerFloorReset(void) {tt_extended=0;tt_reward_pending=0;}
void ME_TowerSave(u8 *out) {
    U32(out,0)=tt_valid?0x3154544d:0;
    for(int i=0;i<9;i++)out[4+i]=tt_order[i];
    out[13]=(u8)tt_extended;out[14]=(u8)(tt_extended>>8);
    u8 *props=(u8*)0x022c6c70+TT_KEY_ALIAS*12;
    for(int i=0;i<12;i++)out[15+i]=tt_extended?props[i]:0;
}
int ME_TowerLoad(const u8 *in) {
    int extended=in[13]|((int)in[14]<<8);
    if(extended && (extended<TT_KEY_FIRST || extended>=TT_KEY_FIRST+8))return 0;
    if(!U32(in,0)) {
        tt_valid=0;tt_extended=extended;tt_reward_pending=0;
        if(extended)tt_restore_properties(in+15);
        return 1;
    }
    if(U32(in,0)!=0x3154544d)return 0;
    int mask=0;
    for(int i=0;i<9;i++) {
        if(in[4+i]>=9 || (mask&(1<<in[4+i])))return 0;
        mask|=1<<in[4+i];
    }
    for(int i=0;i<9;i++)tt_order[i]=in[4+i];
    tt_valid=1;tt_extended=extended;tt_reward_pending=0;
    if(extended)tt_restore_properties(in+15);
    return 1;
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

static int tt_key_room(void) {
    u8 *d=dungeon();
    if(!d || BYTE(d,0x748)!=TT_DUNGEON)return -1;
    if(BYTE(d,0x40da)!=TT_KEY_ALIAS)return -1;
    int room=tt_extended-TT_KEY_FIRST;
    return room>=0 && room<8?room:-1;
}
int ME_TowerChooseKey(void) {
    u8 *d=dungeon();
    if(!d || BYTE(d,0x748)!=TT_DUNGEON)return 0;
    tt_extended=TT_KEY_FIRST+FN(0x022eaa98,int(*)(int))(8);
    return TT_KEY_ALIAS;
}
/* The SIR0 content prefix holds versioned properties for physical rooms256+.
 * Native u8 dungeon fields use an otherwise unused bridge slot. Rebinding
 * its pointer makes every native preload/generation reader see the selected
 * actual layout, without truncating the extended ID or sharing boss rooms. */
void ME_TowerFixedLoaded(void) {
    if(tt_extended<TT_KEY_FIRST || tt_extended>=TT_KEY_FIRST+8)return;
    u8 *d=dungeon();if(!d || BYTE(d,0x748)!=TT_DUNGEON)return;
    u8 *context=*(u8**)0x02353794;if(!context)return;
    u8 *raw=(u8*)U32(context,0);u32 *table=(u32*)U32(context,8);
    if(!raw || !table || U32(raw,16)!=0x3158464d || U32(raw,20)!=1 ||
       U16(raw,24)!=TT_KEY_FIRST || U16(raw,26)!=8 || U16(raw,28)!=TT_KEY_ALIAS)return;
    table[TT_KEY_ALIAS]=table[tt_extended];
    u8 *props=raw+32+(tt_extended-TT_KEY_FIRST)*12;
    tt_restore_properties(props);
}
/* Static fixed-room rows supply safe existing entities. Transform their items
 * only at this dungeon's dedicated placement call, retaining native spawning. */
int ME_TowerItem(int item,int x,int y,u32 *flags) {
    int room=tt_key_room();if(room<0)return item;
    flags[0]=flags[1]=0; /* clean rewards; never replace owned items with seeds */
    if(item!=136)return item;
    static const u16 rewards[8]={99,73,103,93,77,136,136,89};
    if(room==6) {tt_reward_pending=1;tt_reward_x=x;tt_reward_y=y;}
    return rewards[room];
}
static int tt_owned(int item) {
    if(FN(0x0200eee0,int(*)(int))(item))return 1;
    u8 *d=dungeon();
    for(int i=0;i<4;i++) {
        u8 *m=monster((u8*)U32(d,0x12b28+i*4));
        if(m && (BYTE(m,0x62)&1) && U16(m,0x66)==item)return 1;
    }
    return 0;
}
static int tt_family(int species) {
    /* MD's explicit base_form_index is the evolution-family root. It already
     * unifies branches, genders and alternate forms; permanent-form MD rows
     * inherit it as well. Do not infer gender from ID arithmetic or follow
     * Alpha's cyclic Giratina form-change pre-evolution links. */
    u8 *md=*(u8**)0x020b09b4;
    if(!md || species<0 || (u32)species>=U32(md,-4))return -1;
    return U16(md,species*68+0x32);
}
int ME_TowerExclusive(void) {
    u8 *m=monster(FN(0x022e9580,u8*(*)(void))());
    if(!m)return 136;
    int root=tt_family(U16(m,2));
    if(root<0)return 136;
    for(int pass=0;pass<2;pass++) {
        int count=0,chosen=0;
        /* item_s_p has 956 native rows, starting at Prism Ruff (444).
         * Types 8/9/10 are species-family three-star items (including hatch
         * and branching families); type 4 is a type three-star item. */
        for(int item=444;item<1400;item++) {
            if(!FN(0x0200e7c0,int(*)(int))(item))continue;
            int type=FN(0x0200e760,int(*)(int))(item);
            if(pass==0?(type<8 || type>10):type!=4)continue;
            int parameter=FN(0x0200e7e8,int(*)(int))(item);
            if(pass==0) {if(tt_family(parameter)!=root)continue;}
            else if(parameter!=BYTE(m,0x5e) && parameter!=BYTE(m,0x5f))continue;
            if(tt_owned(item))continue;
            /* Reservoir sampling: every distinct eligible item has 1/N odds. */
            count++;
            if(FN(0x022eaa98,int(*)(int))(count)==0)chosen=item;
        }
        if(count)return chosen;
    }
    return 136;
}
/* Fixed-room generation precedes SpawnTeam. Resolve its single placeholder
 * after the current leader and every teammate's held item are available. */
void ME_TowerResolveReward(void) {
    if(!tt_reward_pending)return;
    tt_reward_pending=0;
    if(tt_key_room()!=6)return;
    u8 *tile=FN(0x023360fc,u8*(*)(int,int))(tt_reward_x,tt_reward_y);
    u8 *e=(u8*)U32(tile,0x10);
    if(!e || U32(e,0)!=3)return; /* native ENTITY_ITEM */
    u8 *item=(u8*)U32(e,0xb4);
    if(item && (BYTE(item,0)&1) && U16(item,4)==136)U16(item,4)=(u16)ME_TowerExclusive();
}
