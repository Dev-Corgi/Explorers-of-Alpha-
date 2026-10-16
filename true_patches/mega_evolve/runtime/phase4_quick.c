/* Stock main quicksave stays at page400, size0x5800. The unclaimed flash
 * tail starts at page488 and has0x1800 bytes. MEK4 uses0x1400, bound to the
 * checked main bytes. Old quicksaves have no marker and retain native loading.
 * No entity pointers are persisted. Actors restore by slot+original species.
 */
enum { QUICK_SIZE=0x1400, QUICK_MAIN=0x5800, QUICK_PAGE=488,
       QUICK_MAGIC=0x344b454d, QUICK_ROWS=1040, QUICK_STRIDE=192 };
_Static_assert(28+sizeof(Extra)-12<=QUICK_STRIDE,"quicksave actor row overflow");
_Static_assert(QUICK_ROWS+COUNT*QUICK_STRIDE+8<=QUICK_SIZE,"quicksave globals overflow");
#ifdef ME_TRIAL_TOWER
_Static_assert(4888+27<=QUICK_SIZE,"extended fixed-room quicksave overflow");
#endif
static u8 quick_pending[QUICK_SIZE];
static int quick_loaded;
static u32 quick_hash(u8 *p,int n,int skip) {
    u32 v=2166136261u;
    for(int i=0;i<n;i++)if(i<skip || i>=skip+4)v=(v^p[i])*16777619u;
    return v;
}
static void quick_copy(u8 *to,const u8 *from,int n) {while(n--)*to++=*from++;}
int ME_QuickWrite(u32 *position,u8 *main,int size) {
    if(*position!=400 || size!=QUICK_MAIN)return FN(0x02048e74,int(*)(u32*,u8*,int))(position,main,size);
    if(depth || effect_depth)return 2;
    int result=FN(0x02048e74,int(*)(u32*,u8*,int))(position,main,size);
    if(result)return result;
    zero(quick_pending,QUICK_SIZE);
    U32(quick_pending,0)=QUICK_MAGIC;U16(quick_pending,4)=1;U16(quick_pending,6)=QUICK_SIZE;
    U32(quick_pending,8)=quick_hash(main,size,size);
    if(ME_ExportState(quick_pending+16,SNAPSHOT)!=SNAPSHOT)return 2;
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i),*m=monster(e);if(!m)continue;
        AbilityBank *b=bank(e);Extra *x=ext(e);if(!b||!x)return 2;
        u8 *row=quick_pending+QUICK_ROWS+i*QUICK_STRIDE;
        U16(row,0)=U16(m,2);U16(row,2)=1;
        quick_copy(row+4,(u8*)b->permanent,12);quick_copy(row+16,(u8*)b->current,12);
        quick_copy(row+28,(u8*)x+12,sizeof(Extra)-12);
    }
    U32(quick_pending,4880)=sunlight_serial;U32(quick_pending,4884)=movement_serial;
#ifdef ME_TRIAL_TOWER
    ME_TowerSave(quick_pending+4888);
#endif
    U32(quick_pending,12)=quick_hash(quick_pending,QUICK_SIZE,12);
    result=FN(0x0204a9c8,int(*)(int,u8*,int))(QUICK_PAGE,quick_pending,QUICK_SIZE);
    quick_loaded=0;
    return result==4?1:result?2:0;
}
int ME_QuickRead(u32 *position,u8 *main,int size) {
    int is_quick=*position==400 && size==QUICK_MAIN;
    int result=FN(0x02048ed0,int(*)(u32*,u8*,int))(position,main,size);
    if(!is_quick || result)return result;
    quick_loaded=0;
    result=FN(0x0204a8e0,int(*)(int,u8*,int))(QUICK_PAGE,quick_pending,QUICK_SIZE);
    if(result)return 2;
    if(U32(quick_pending,0)!=QUICK_MAGIC)return 0;
    if(U16(quick_pending,4)!=1 || U16(quick_pending,6)!=QUICK_SIZE ||
       U32(quick_pending,8)!=quick_hash(main,size,size) ||
       U32(quick_pending,12)!=quick_hash(quick_pending,QUICK_SIZE,12))return 2;
    u8 *component=quick_pending+16;
    if(U32(component,0)!=MAGIC || U16(component,4)!=SCHEMA ||
       U16(component,6)!=SNAPSHOT || U32(component,12)!=checksum(component))return 2;
    for(int i=0;i<COUNT;i++)if(BYTE(component,16+i*4+3) &&
       (BYTE(component,16+i*4+2)<4 || BYTE(component,16+i*4+2)>16))return 2;
    for(int i=0;i<SOURCES;i++) {
        u8 *s=component+96+i*12;int weather=BYTE(s,4);
        if(BYTE(s,1) && (BYTE(s,0)>=COUNT || !known(U16(s,2)) ||
           BYTE(s,5)>1 || BYTE(s,6)>2 ||
           (weather!=0 && weather!=1 && weather!=2 && weather!=4 && weather!=5)))return 2;
    }
    for(int i=0;i<COUNT;i++) {
        u8 *row=quick_pending+QUICK_ROWS+i*QUICK_STRIDE;
        if(U16(row,2)>1)return 2;
        if(!U16(row,2))continue;
        for(int j=0;j<6;j++)if(!packed_valid(U32(row,4+j*4)))return 2;
    }
#ifdef ME_TRIAL_TOWER
    if(!ME_TowerLoad(quick_pending+4888))return 2;
#endif
    quick_loaded=1;return 0;
}
static void ME_QuickActor(u8 *e) {
    if(!quick_loaded)return;
    int i=slot(e);u8 *m=monster(e);if(i<0||!m)return;
    u8 *row=quick_pending+QUICK_ROWS+i*QUICK_STRIDE;
    if(!U16(row,2)||U16(row,0)!=U16(m,2))return;
    AbilityBank *b=bank(e);Extra *x=ext(e);if(!b||!x)return;
    quick_copy((u8*)b->permanent,row+4,12);quick_copy((u8*)b->current,row+16,12);
    b->configured=1;publish(b);
    quick_copy((u8*)x+12,row+28,sizeof(Extra)-12);
    /* Old action tokens cannot address a fresh action ledger. */
    x->conversion_action=x->charge_action=0;x->conversion_valid=0;
}
void ME_QuickReady(void) {
    if(!quick_loaded)return;
#ifdef ME_TRIAL_TOWER
    /* Native floor initialization can run after the sidecar read. Reapply the
     * validated room ID/properties after that reset, before the first turn. */
    ME_TowerLoad(quick_pending+4888);
#endif
    for(int i=0;i<COUNT;i++)ME_QuickActor(entity(i));
    ME_ImportState(quick_pending+16,SNAPSHOT);
    sunlight_serial=U32(quick_pending,4880);movement_serial=U32(quick_pending,4884);
    quick_loaded=0;
}
