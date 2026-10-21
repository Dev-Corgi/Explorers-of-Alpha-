#include "generated.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

enum { MEMBERS=559, GROUND_MEMBERS=555, SLOTS=4, RECORD_BYTES=MEMBERS*SLOTS*4,
       BLOCK_BYTES=0x2300, MAGIC=0x31564C4D,
       PAGE0=400, PAGE200=440 };

typedef struct { u16 move[SLOTS]; u16 mastery[SLOTS]; } Record;
typedef struct {
    Record record[MEMBERS];
    u8 action_awarded[MEMBERS];
} State;

#define FN(a,t) ((t)(a))
#define state ((State *)STATE_ADDRESS)
#define active FN(0x0205638C,u8 *(*)(int))
#define ground FN(0x020555A8,u8 *(*)(int))
#define original_read FN(ORIGINAL_READ,int (*)(u32 *,u8 *,u32))
#define original_write FN(ORIGINAL_WRITE,int (*)(u32 *,u8 *,u32))
#define raw_read FN(0x0204A8E0,int (*)(u32,u8 *,u32))
#define raw_write FN(0x0204A9C8,int (*)(u32,u8 *,u32))
#define alloc FN(0x02001170,void *(*)(u32,u32))
#define free_mem FN(0x02001188,void (*)(void *))
#define checksum FN(0x02048F24,void (*)(u8 *,u32))
#define invalid_checksum FN(0x02048F4C,int (*)(u8 *,u32))
#define MoveLevel_PriorSaveRead FN(PRIOR_SAVE_READ,int (*)(u32 *,u8 *,u32))
#define MoveLevel_PriorSaveWrite FN(PRIOR_SAVE_WRITE,int (*)(u32 *,u8 *,u32))
#define MoveLevel_PriorNewGame FN(PRIOR_NEW_GAME,void (*)(void))

static void zero(u8 *p,u32 n){while(n--)*p++=0;}
static void copy(u8 *d,const u8 *s,u32 n){while(n--)*d++=*s++;}
static int blank_block(const u8 *p,u32 n){
    u8 erased=p[0];if(erased!=0&&erased!=0xFF)return 0;
    while(n--)if(*p++!=erased)return 0;
    return 1;
}
static u16 rd16(const u8 *p){return (u16)p[0]|((u16)p[1]<<8);}

static int entity_id(u8 *e,u8 **mout){
    if(!e || *(u32 *)e!=1) return -1;
    u8 *m=*(u8 **)(e+0xB4); if(!m) return -1;
    int slot=(short)rd16(m+12); if(slot<0 || slot>=4) return -1;
    u8 *t=active(slot); if(!t || !(t[0]&1)) return -1;
    int id=(short)rd16(t+8); if(id<0 || id>=MEMBERS) return -1;
    if(mout)*mout=m;
    return id;
}
static int ground_id(u8 *g){
    for(int i=0;i<GROUND_MEMBERS;i++) if(ground(i)==g)return i;
    return -1;
}
static int level(u16 v){return v>=700?3:v>=300?2:v>=100?1:0;}
static u8 *real_move(u8 *e,u8 *move){
    if(!move) return 0;
    if(*(u16 *)(move+4)!=559) return move;
    if(*(volatile u8 *)TM_PENDING) return 0;
    if(!*(volatile u8 *)Z_PENDING) return move;
    u8 *m=*(u8 **)(e+0xB4); if(!m)return move;
    int slot=*(volatile u8 *)Z_SELECTED_SLOT; if(slot<0||slot>=4)return move;
    return m+0x124+slot*8;
}
static void sync_entity(u8 *e,int *id_out,u8 **mout){
    u8 *m=0; int id=entity_id(e,&m); if(id<0){if(id_out)*id_out=-1;return;}
    for(int j=0;j<SLOTS;j++){
        u8 *mv=m+0x124+j*8; u16 mid=rd16(mv+4);
        if(state->record[id].move[j]!=mid){state->record[id].move[j]=mid;state->record[id].mastery[j]=0;}
        mv[7]=(u8)level(state->record[id].mastery[j]);
    }
    if(id_out)*id_out=id;
    if(mout)*mout=m;
}
static int slot_for(u8 *m,u8 *move){
    for(int j=0;j<SLOTS;j++)if(m+0x124+j*8==move)return j;
    for(int j=0;j<SLOTS;j++)if(rd16(m+0x124+j*8+4)==rd16(move+4))return j;
    return -1;
}
static void set_item_level(u8 *e,int max_level){
    u8 *m=0;int id=-1;sync_entity(e,&id,&m);if(id<0)return;
    int slot=-1;
    for(int j=0;j<SLOTS;j++) if(m[0x124+j*8]&1){slot=j;break;}
    if(slot<0)return;
    u32 v=state->record[id].mastery[slot];
    if(max_level)v=700;
    else if(v<100)v=100;else if(v<300)v=300;else v=700;
    state->record[id].mastery[slot]=(u16)v;
    m[0x124+slot*8+7]=(u8)level((u16)v);
}

void MoveLevel_BeginAction(u8 *e){int id=entity_id(e,0);if(id>=0)state->action_awarded[id]=0;sync_entity(e,0,0);}
int MoveLevel_GetLevelForMove(u8 *e,u8 *move){
    if(!e || !move || *(volatile u8 *)TM_PENDING)return 0;
    u8 *m=0;int id=-1;sync_entity(e,&id,&m);if(id<0)return 0;
    u8 *actual=real_move(e,move);if(!actual)return 0;
    int slot=slot_for(m,actual);return slot<0?0:level(state->record[id].mastery[slot]);
}
int MoveLevel_ScalePower(u8 *e,u8 *move,int base){
    int l=MoveLevel_GetLevelForMove(e,move);return (base*(100+10*l))/100;
}
void MoveLevel_OnHit(u8 *e,u8 *move,int result){
    if(result!=1 || !e || !move || *(volatile u8 *)TM_PENDING)return;
    u8 *m=0;int id=-1;sync_entity(e,&id,&m);if(id<0||state->action_awarded[id])return;
    u8 *actual=real_move(e,move);if(!actual)return;int slot=slot_for(m,actual);if(slot<0)return;
    state->action_awarded[id]=1;
    u32 v=state->record[id].mastery[slot]+4;if(v>700)v=700;state->record[id].mastery[slot]=(u16)v;
    m[0x124+slot*8+7]=(u8)level((u16)v);
}

int MoveLevel_GetMaxPp(u8 *move){
    if(!move)return 0;
    int base=FN(0x02013A30,int (*)(u8 *))(move);
    int l=(*(u8 *)(move+7)>3)?3:*(u8 *)(move+7);
    int out=(base*(100+10*l)+99)/100;return out>99?99:out;
}

int MoveLevel_GinsengGround(u8 *g,u16 *move_out,u8 *boost_out){
    int id=ground_id(g);if(id<0)return 0;
    int slot=-1;
    for(int j=0;j<SLOTS;j++) if(g[0x22+j*6]&1){slot=j;break;}
    if(slot<0)return 0;
    u8 *gm=g+0x22+slot*6;
    u16 mid=rd16(gm+2);
    if(state->record[id].move[slot]!=mid){state->record[id].move[slot]=mid;state->record[id].mastery[slot]=0;}
    u32 v=state->record[id].mastery[slot];
    if(v>=700)return 0;
    if(v<100)v=100;else if(v<300)v=300;else v=700;
    state->record[id].mastery[slot]=(u16)v;
    gm[4]=(u8)level((u16)v);
    if(move_out)*move_out=mid;
    if(boost_out)*boost_out=(u8)level((u16)v);
    return 1;
}
void MoveLevel_ItemGinseng(u8 *e,u8 *item){
    if(!e||!item)return;
    u16 id=rd16(item+4);
    if(id==88)set_item_level(e,0);
    else if(id==98||id==349)set_item_level(e,1);
}

static void block_make(u8 *b){
    zero(b,BLOCK_BYTES);((u32 *)b)[1]=MAGIC;((u16 *)b)[4]=1;((u16 *)b)[5]=MEMBERS;
    copy(b+16,(u8 *)state,RECORD_BYTES);checksum(b,BLOCK_BYTES);
}
static int block_load(u32 page){
    u8 *b=alloc(BLOCK_BYTES,5);if(!b)return 2;int r=raw_read(page,b,BLOCK_BYTES);
    if(r)r=2;
    else if(blank_block(b,BLOCK_BYTES))r=0; /* Save predates move_level (schema 0). */
    else if(invalid_checksum(b,BLOCK_BYTES)||((u32 *)b)[1]!=MAGIC||((u16 *)b)[4]!=1||((u16 *)b)[5]!=MEMBERS)r=2;
    else copy((u8 *)state,b+16,RECORD_BYTES);
    free_mem(b);
    return r;
}
static int block_save(u32 page){
    u8 *b=alloc(BLOCK_BYTES,5);if(!b)return 2;block_make(b);int r=raw_write(page,b,BLOCK_BYTES);free_mem(b);return r==4?1:r?2:0;
}
int MoveLevel_SaveRead(u32 *pos,u8 *main,u32 size){u32 start=*pos;int r=MoveLevel_PriorSaveRead(pos,main,size);if(r||size!=0xB65C||(start!=0&&start!=200))return r;zero((u8 *)state,sizeof(State));return block_load(start==0?PAGE0:PAGE200);}
int MoveLevel_SaveWrite(u32 *pos,u8 *main,u32 size){u32 start=*pos;int r=MoveLevel_PriorSaveWrite(pos,main,size);if(r||size!=0xB65C||(start!=0&&start!=200))return r;return block_save(start==0?PAGE0:PAGE200);}
void MoveLevel_NewGame(void){MoveLevel_PriorNewGame();zero((u8 *)state,sizeof(State));}
