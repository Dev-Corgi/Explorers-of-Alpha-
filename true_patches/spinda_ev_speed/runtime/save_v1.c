/* Alpha+ doping schema. Canonical V bytes in RAM contain permanent + outing V.
 * The stock monster stream contains permanent V only; its 10-bit HP field is
 * deliberately unchanged. Full Speed and all outing V live in the slot tail.
 * Built freestanding for ARM946E-S; all addresses below are vanilla functions,
 * never code-cave placements. Cave state/trampolines come from generated.h.
 */
#include "generated.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
enum { MEMBERS=555, MAZE=4, MAIN_SIZE=0xB65C, TAIL_OFF=0xB700,
       TAIL_SIZE=3908, WRITE_SIZE=TAIL_OFF+TAIL_SIZE, MAGIC=0x31535645 };
typedef struct {
    u8 temporary[MEMBERS][6]; /* HP, Atk, SpA, Def, SpD, Speed */
    u8 speed[MEMBERS+MAZE];
    u8 loaded, legacy, depth, pad;
    u8 before[6];
    u8 *entity;
} State;
#define FN(address, type) ((type)(address))
#define alloc FN(0x02001170, void *(*)(u32,u32))
#define free_mem FN(0x02001188, void (*)(void *))
#define ground FN(0x020555A8, u8 *(*)(int))
#define active FN(0x0205638C, u8 *(*)(int))
#define original_read FN(ORIGINAL_READ, int (*)(u32 *,u8 *,u32))
#define original_write FN(ORIGINAL_WRITE, int (*)(u32 *,u8 *,u32))
#define original_copy FN(ORIGINAL_COPY, void (*)(void *,u8 *))
#define original_monsters FN(ORIGINAL_MONSTERS, int (*)(u8 *,u32))
#define raw_read FN(0x0204A8E0, int (*)(u32,u8 *,u32))
#define raw_write FN(0x0204A9C8, int (*)(u32,u8 *,u32))
#define checksum FN(0x02048F24, void (*)(u8 *,u32))
#define invalid_checksum FN(0x02048F4C, int (*)(u8 *,u32))
static const u8 offsets[6]={10,12,13,14,15,11};
static void copy(u8 *to,const u8 *from,u32 n) { while(n--) *to++=*from++; }
static void zero(u8 *to,u32 n) { while(n--) *to++=0; }
static State *state(void) {
    /* Resident zero-initialized cave RAM, independent of dungeon heap resets. */
    return (State *)STATE_ADDRESS;
}
static u16 half(const u8 *p) { return p[0]|(p[1]<<8); }
static int index_of(const u8 *g) {
    u8 *base=*(u8 **)0x020B0A48;
    /* Avoid division helpers and reject pointers outside the roster. */
    for(int i=0;i<MEMBERS;i++,base+=0x44) if(g==base) return i;
    return -1;
}
static u8 *maze(int i) { return *(u8 **)0x020B0A48+0x9898+i*0x44; }
static int entity_values(u8 *e,u8 *values,u8 **team_out) {
    if(!e || *(u32 *)e!=1) return -1;
    u8 *m=*(u8 **)(e+0xB4);
    if(!m) return -1;
    int slot=(s16)half(m+12);
    if(slot<0 || slot>=4) return -1;
    u8 *t=active(slot);
    if(!t || !(t[0]&1)) return -1;
    int id=(s16)half(t+8);
    if(id<0 || id>=MEMBERS) return -1;
    values[0]=t[16]; values[5]=t[17];
    for(int j=1;j<5;j++) values[j]=m[25+j];
    *team_out=t;
    return id;
}
void EvSave_Begin(u8 *entity) {
    State *s=state(); u8 *team;
    if(!s) return;
    if(!s->depth) {
        s->entity=entity;
        if(entity_values(entity,s->before,&team)<0) s->entity=0;
    }
    s->depth++;
}
void EvSave_End(void) {
    State *s=state(); u8 now[6],*t;
    if(!s || !s->depth || --s->depth || !s->entity) return;
    int id=entity_values(s->entity,now,&t);
    if(id<0) return;
    u8 *g=ground(id);
    for(int j=0;j<6;j++) {
        int delta=(int)now[j]-s->before[j];
        int tmp=s->temporary[id][j]+delta;
        if(tmp<0) tmp=0;
        if(tmp>now[j]) tmp=now[j];
        s->temporary[id][j]=tmp;
        g[offsets[j]]=now[j];
        t[j==0?16:j==5?17:17+j]=now[j];
    }
    s->entity=0;
}
void EvSave_CopyMonster(void *stream,u8 *g) {
    State *s=state(); u8 local[0x44];
    copy(local,g,sizeof(local));
    int id=index_of(g);
    if(s && id>=0) for(int j=0;j<6;j++) {
        int value=(int)local[offsets[j]]-s->temporary[id][j];
        local[offsets[j]]=value<0?0:value;
    }
    /* Stock HP serialization is still 10 bits. The tail owns all Speed bits. */
    local[11]=0;
    original_copy(stream,local);
}
static int marked(const u8 *main) { return main[0x35]=='E' && main[0x36]=='V' && main[0x37]==1; }
static void make_tail(u8 *tail,const u8 *main,State *s) {
    zero(tail,TAIL_SIZE);
    ((u32 *)tail)[1]=MAGIC;
    ((u32 *)tail)[2]=*(u32 *)main;
    ((u16 *)tail)[6]=1; ((u16 *)tail)[7]=MEMBERS;
    for(int i=0;i<MEMBERS;i++) {
        u8 *g=ground(i);
        if(!(g[0]&1)) continue;
        int speed=(int)g[11]-s->temporary[i][5];
        tail[16+i]=speed<0?0:speed;
        copy(tail+16+MEMBERS+MAZE+i*6,s->temporary[i],6);
    }
    for(int i=0;i<MAZE;i++) tail[16+MEMBERS+i]=maze(i)[11];
    checksum(tail,TAIL_SIZE);
}
int EvSave_Write(u32 *position,u8 *main,u32 size) {
    if(size!=MAIN_SIZE || (*position!=0 && *position!=200)) return original_write(position,main,size);
    State *s=state();
    /* An unmarked save needs the user's import choice before it can be saved. */
    if(!s || s->legacy) return 2;
    u8 *buffer=alloc(WRITE_SIZE,5);
    if(!buffer) return 2;
    zero(buffer,WRITE_SIZE); copy(buffer,main,MAIN_SIZE);
    buffer[0x35]='E'; buffer[0x36]='V'; buffer[0x37]=1;
    checksum(buffer,MAIN_SIZE);
    make_tail(buffer+TAIL_OFF,buffer,s);
    int result=raw_write(*position,buffer,WRITE_SIZE);
    *position+=(WRITE_SIZE+255)>>8;
    free_mem(buffer);
    return result==4?1:result?2:0;
}
int EvSave_Read(u32 *position,u8 *main,u32 size) {
    u32 start=*position;
    int result=original_read(position,main,size);
    if(size!=MAIN_SIZE || (start!=0 && start!=200) || result) return result;
    State *s=state();
    if(!s) return 2;
    zero((u8 *)s,sizeof(State));
    if(!marked(main)) {
        if(main[0x35]=='E' && main[0x36]=='V') return 2; /* future schema */
        s->legacy=1; return 0;
    }
    u8 *tail=alloc(TAIL_SIZE,5);
    if(!tail) return 2;
    result=raw_read(start+(TAIL_OFF>>8),tail,TAIL_SIZE);
    if(result || invalid_checksum(tail,TAIL_SIZE) || ((u32 *)tail)[1]!=MAGIC ||
       ((u32 *)tail)[2]!=*(u32 *)main || ((u16 *)tail)[6]!=1 || ((u16 *)tail)[7]!=MEMBERS) result=2;
    else {
        copy(s->speed,tail+16,MEMBERS+MAZE);
        copy((u8 *)s->temporary,tail+16+MEMBERS+MAZE,MEMBERS*6);
        s->loaded=1;
    }
    free_mem(tail);
    return result;
}
int EvSave_ReadMonsters(u8 *buffer,u32 size) {
    int result=original_monsters(buffer,size);
    State *s=state();
    if(!s || !s->loaded) return result;
    for(int i=0;i<MEMBERS;i++) {
        u8 *g=ground(i);
        if(!(g[0]&1)) { zero(s->temporary[i],6); continue; }
        g[11]=s->speed[i];
        for(int j=0;j<6;j++) {
            int total=g[offsets[j]]+s->temporary[i][j];
            g[offsets[j]]=total>255?255:total;
        }
    }
    for(int i=0;i<MAZE;i++) maze(i)[11]=s->speed[MEMBERS+i];
    s->loaded=0;
    s->pad=1; /* reconcile quicksave copies at the first playable turn */
    return result;
}
int EvSave_LegacyPending(void) { State *s=state(); return s?s->legacy:0; }
/* choice 0 imports Alpha; choice 1 retains old Alpha+ permanent doping. */
void EvSave_Convert(int choice) {
    State *s=state(); if(!s || !s->legacy || (choice!=0 && choice!=1)) return;
    if(!choice) {
        for(int i=0;i<MEMBERS;i++) zero(ground(i)+10,6);
        for(int i=0;i<MAZE;i++) zero(maze(i)+10,6);
        u8 *base=*(u8 **)0x020B0A48+0x936C;
        for(int i=0;i<12;i++,base+=0x68) zero(base+16,6);
    }
    zero((u8 *)s,sizeof(State));
}
void EvSave_GroupEnd(void) {
    State *s=state(); if(!s) return;
    for(int i=0;i<MEMBERS;i++) {
        u8 *g=ground(i);
        if(g[0]&1) for(int j=0;j<6;j++) {
            int permanent=(int)g[offsets[j]]-s->temporary[i][j];
            g[offsets[j]]=permanent<0?0:permanent;
        }
        zero(s->temporary[i],6);
    }
    /* Copy by guild member ID, across all three active team rosters. */
    u8 *t=*(u8 **)0x020B0A48+0x936C;
    for(int i=0;i<12;i++,t+=0x68) {
        int id=(s16)half(t+8);
        if((t[0]&1) && id>=0 && id<MEMBERS) {
            u8 *g=ground(id);
            for(int j=0;j<6;j++) t[j==0?16:j==5?17:17+j]=g[offsets[j]];
        }
    }
}
void EvSave_NewGame(void) { State *s=state(); if(s) zero((u8 *)s,sizeof(State)); }

/* Older dungeon quicksaves can bypass the ground updater coroutine. Ask at
 * the first playable leader turn, when dungeon dialogue/UI is initialized.
 * Two confirmations mean B/No never silently selects a conversion policy.
 */
void EvSave_DungeonImport(void) {
    State *s=state();
    if(!s || (!s->legacy && !s->pad)) return;
    int legacy=s->legacy;
    int choice;
    if(legacy) {
        for(;;) {
            if(FN(0x0234D518,int (*)(void *,int,int,int,int))(0,19611,1,1,1)==1) { choice=0; break; }
            if(FN(0x0234D518,int (*)(void *,int,int,int,int))(0,19612,1,1,1)==1) { choice=1; break; }
        }
        EvSave_Convert(choice);
    }
    s->pad=0;
    /* Legacy quicksave monster copies still contain the old stat format.
     * Reconcile them by roster ID after the explicitly selected conversion.
     */
    u8 *d=*(u8 **)0x02353538;
    if(!d) return;
    for(int slot=0;slot<4;slot++) {
        u8 *e=*(u8 **)(d+0x12B28+slot*4), values[6],*t;
        int id=entity_values(e,values,&t);
        if(id<0) continue;
        u8 *g=ground(id),*m=*(u8 **)(e+0xB4);
        for(int j=0;j<6;j++) t[j==0?16:j==5?17:17+j]=g[offsets[j]];
        for(int j=0;j<4;j++) m[26+j]=g[12+j];
        if(legacy) {
            int hp=FN(CALC_STAT,int (*)(int,int,int,int))((s16)half(m+2),m[10],0,g[10]);
            m[18]=hp; m[19]=hp>>8;
            int maximum=hp+(s16)half(m+22);
            if((s16)half(m+16)>maximum) { m[16]=maximum; m[17]=maximum>>8; }
        }
    }
}
