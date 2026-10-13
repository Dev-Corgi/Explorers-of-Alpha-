/* Shared normal-effect services. Grade-specific deltas are recorded in phase3.json;
 * enhanced individual effects are enabled by phase7, not by presentation text. */
#include "phase3_items_generated.h"
#include "phase3_moves_generated.h"

int ME_KeepBerry(u8 *consumer,u8 *item) {
    if(!alive(consumer)||!item||!(BYTE(item,0)&1))return 0;
    int berry=0;
    for(unsigned i=0;i<sizeof(berry_items)/sizeof(berry_items[0]);i++)if(U16(item,4)==berry_items[i])berry=1;
    if(!berry)return 0;
    if(has(consumer,A_CUD_CHEW)&&FN(0x022eab20,int(*)(int))(20))return 1;
    return has(consumer,A_HARVEST)&&FN(0x022eab20,int(*)(int))(ME_ApparentWeather(consumer)==1?25:12);
}
int ME_PickupItem(u8 *e) {
    u8 *m=monster(e);
    if(!alive(e)||BYTE(m,6)||!has(e,A_PICKUP)||FN(0x0200edc0,int(*)(void))())return 0;
    if(!FN(0x022eab20,int(*)(int))(50))return 0;
    int index=FN(0x022eaa98,int(*)(int))(sizeof(pickup_items)/sizeof(pickup_items[0]));
    if(index<0||index>=(int)(sizeof(pickup_items)/sizeof(pickup_items[0])))return 0;
    u8 item[6];zero(item,sizeof(item));
    FN(0x023443b4,void(*)(u8*,int,int,int))(item,pickup_items[index],1,0);
    return FN(0x0200f874,int(*)(u8*))(item);
}

const BaseProfile *ME_FindProfile(int species) {
    int lo=0,hi=(int)(sizeof(base_profiles)/sizeof(base_profiles[0]));
    while(lo<hi) {int mid=(lo+hi)/2;if(base_profiles[mid].species<species)lo=mid+1;else hi=mid;}
    return lo<(int)(sizeof(base_profiles)/sizeof(base_profiles[0])) && base_profiles[lo].species==species?&base_profiles[lo]:0;
}
static int defhas(u8 *actor,u8 *target,int id) {
    return FN(0x022f96cc,int(*)(u8*,u8*,int,int))(actor,target,id,1);
}
static int adjacent(u8 *a,u8 *b) {
    int dx=(s16)U16(a,4)-(s16)U16(b,4),dy=(s16)U16(a,6)-(s16)U16(b,6);
    return dx>=-1&&dx<=1&&dy>=-1&&dy<=1;
}
static int friends(u8 *a,u8 *b) {
    u8 *x=monster(a),*y=monster(b);
    return x&&y&&((BYTE(x,6)^BYTE(x,8))==(BYTE(y,6)^BYTE(y,8)));
}
static int room(u8 *a,u8 *b) {return BYTE(a,0x25)!=255 && BYTE(a,0x25)==BYTE(b,0x25);}
static int maxhp(u8 *e) {u8 *m=monster(e);return m?clamp((s16)U16(m,0x12)+(s16)U16(m,0x16),1,32767):1;}
static int hp(u8 *e) {u8 *m=monster(e);return m?(s16)U16(m,0x10):0;}
static int multiply(int value,int n,int d) {return clamp(divide(value*n,d),0,32767);}
/* Floor-local state. The persistent profile is owned by the bank, never here. */
typedef struct {u32 entity,monster,floor,once; u16 locked_move;u8 charged,pad;u32 sun_serial;
    u32 conversion_action,charge_action,moved_epoch,stake_used[COUNT];
    u16 conversion_move;u8 conversion_type,conversion_valid,moved_ready,sun_seen;
    u8 tailwind_mask,tailwind_remaining[5];} Extra;
static Extra *extra;
static u32 sunlight_serial,movement_serial;
static int movement_context,calculation_context;
static int speed_move_context;
typedef struct {u8 *actor,*target;} Calculation;
static Calculation calculations[16];
static Extra *ext(u8 *e) {
    ensure();
    if(!extra) {
        extra=FN(0x02001170,void*(*)(int,int))(sizeof(Extra)*COUNT,0);
        if(!extra)return 0;
        zero(extra,sizeof(Extra)*COUNT);
    }
    int i=slot(e);u8 *m=monster(e);if(i<0||!m)return 0;
    Extra *x=&extra[i];
    if(x->entity!=(u32)e||x->monster!=(u32)m||x->floor!=state.floor) {
        zero(x,sizeof(*x));x->entity=(u32)e;x->monster=(u32)m;x->floor=state.floor;
    }
    return x;
}
static void prune_tailwind(Extra *x,u8 *m) {
    for(int i=0;i<5;i++)if(x->tailwind_mask&(1<<i)) {
        int counter=BYTE(m,0x114+i);
        if(!counter||counter>x->tailwind_remaining[i])x->tailwind_mask&=~(1<<i);
        else x->tailwind_remaining[i]=(u8)counter;
    }
}
int ME_EnterSpeedMove(u8 *move) {
    int previous=speed_move_context;
    speed_move_context=move&&U16(move,4)==444;
    return previous;
}
void ME_LeaveSpeedMove(int previous) {speed_move_context=previous;}
void ME_SpeedMoveApplied(u8 *target,u32 previous_four,u32 previous_last) {
    if(!alive(target))return;
    Extra *x=ext(target);u8 *m=monster(target);if(!x)return;
    /* Expired or externally overwritten slots cannot own a Tailwind anymore.
     * Compare BEFORE the native writer to identify slot reuse by other speed
     * sources even if their random duration happens to match the old value. */
    for(int i=0;i<5;i++) {
        int before=i==4?(int)previous_last:(int)((previous_four>>(i*8))&255);
        if((x->tailwind_mask&(1<<i))&&(!before||before>x->tailwind_remaining[i]))
            x->tailwind_mask&=~(1<<i);
    }
    int active=x->tailwind_mask!=0;
    for(int i=0;i<5;i++) {
        int before=i==4?(int)previous_last:(int)((previous_four>>(i*8))&255);
        int after=BYTE(m,0x114+i);
        if(after!=before) {
            x->tailwind_mask&=~(1<<i);
            if(speed_move_context&&after) {
                x->tailwind_mask|=1<<i;x->tailwind_remaining[i]=(u8)after;
            }
        }
    }
    prune_tailwind(x,m);
    if(speed_move_context&&!active&&x->tailwind_mask&&has(target,A_WIND_RIDER))
        ME_ChangeStat(target,target,0,1);
}
void ME_ActorStarts(u8 *e) {Extra *x=ext(e);if(x)x->moved_ready=0;}
void ME_ActorFinishes(u8 *e,u32 old_position,int action) {
    Extra *x=ext(e);
    if(!alive(e)||!x||action!=2||U32(e,4)==old_position)return;
    if(!++movement_serial) {
        movement_serial=1;
        for(int i=0;i<COUNT;i++)zero(extra[i].stake_used,sizeof(extra[i].stake_used));
    }
    x->moved_epoch=movement_serial;x->moved_ready=1;
}
static int stakeout_ready(u8 *a,u8 *b) {
    if(friends(a,b)||!has(a,A_STAKEOUT))return 0;
    Extra *owner=ext(a),*target=ext(b);int index=slot(b);
    return owner&&target&&index>=0&&target->moved_ready&&owner->stake_used[index]!=target->moved_epoch;
}
static int safe_escape_tile(int x,int y) {
    if(x<=0||y<=0||x>=55||y>=31)return 0;
    u8 *tile=FN(0x02336164,u8*(*)(int,int))(x,y);
    /* Floor terrain only; no stairs, monsters, items or hidden traps. */
    return tile&&(U16(tile,0)&7)==1&&!U32(tile,0xc)&&!U32(tile,0x10);
}
int ME_RunAway(u8 *actor,u8 *holder,int previous_hp) {
    Extra *x=ext(holder);
    if(!alive(holder)||!monster(actor)||friends(actor,holder)||!x||(x->once&4)||
       hp(holder)>=previous_hp||hp(holder)>divide(maxhp(holder),4)||!has(holder,A_RUN_AWAY))return 0;
    int visited[COUNT];zero(visited,sizeof(visited));int target_x=-1,target_y=-1;
    for(int attempt=0;attempt<COUNT&&target_x<0;attempt++) {
        int selected=-1,best=65536;
        for(int i=0;i<COUNT;i++) {
            u8 *ally=entity(i);
            if(visited[i]||ally==holder||!alive(ally)||!friends(ally,holder))continue;
            int dx=(s16)U16(ally,4)-(s16)U16(holder,4),dy=(s16)U16(ally,6)-(s16)U16(holder,6);
            if(dx<0)dx=-dx;
            if(dy<0)dy=-dy;
            int distance=dx>dy?dx:dy;
            if(distance<best)best=distance,selected=i;
        }
        if(selected<0)break;
        visited[selected]=1;u8 *ally=entity(selected);
        for(int dy=-1;dy<=1&&target_x<0;dy++)for(int dx=-1;dx<=1;dx++) {
            if(!dx&&!dy)continue;
            int px=(s16)U16(ally,4)+dx,py=(s16)U16(ally,6)+dy;
            if(safe_escape_tile(px,py)) {target_x=px;target_y=py;break;}
        }
    }
    if(target_x<0)for(int py=1;py<31&&target_x<0;py++)for(int px=1;px<55;px++)
        if(safe_escape_tile(px,py)) {target_x=px;target_y=py;break;}
    if(target_x<0)return 0;
    FN(0x022f85f0,void(*)(u8*,int,int,int))(holder,target_x,target_y,1);
    if((s16)U16(holder,4)!=target_x||(s16)U16(holder,6)!=target_y)return 0;
    x->once|=4;return 1;
}
/* Shape-specific and ability-change immune identities. Inspect the actual
 * slots even when suppression is active; suppression cannot make a protected
 * permanent identity transferable. Unassigned legacy Illusion251 is retained. */
static int protected_identity(int id) {
    static const u8 protected[]={37,116,125,166,179,183,189,190,206,207,208,229,230,241,243,247,250,251};
    int legacy=effect(id);
    for(unsigned j=0;j<sizeof(protected);j++)if(legacy==protected[j])return 1;
    return 0;
}
static int protected_profile(AbilityBank *b) {
    for(int i=0;i<3;i++)if(protected_identity(b->current[i]&65535))return 1;
    return 0;
}
static void queue_faint_copy(u8 *holder,u8 *source) {
    int owner=slot(holder),origin=slot(source);
    if(!ability_memory||!depth||owner<0||origin<0||!room(holder,source)||
       !friends(holder,source)||!has(holder,A_POWER_OF_ALCHEMY))return;
    AbilityBank *a=bank(holder),*b=bank(source);if(!a||!b)return;
    int own=-1;for(int i=0;i<3;i++)if((a->current[i]&65535)==A_POWER_OF_ALCHEMY&&own<0)own=i;
    if(own<0)return;
    Action *action=&actions[depth-1];
    int dx=(s16)U16(holder,4)-(s16)U16(source,4),dy=(s16)U16(holder,6)-(s16)U16(source,6);
    if(dx<0)dx=-dx;
    if(dy<0)dy=-dy;
    int distance=dx>dy?dx:dy;
    if(action->copies[owner].ability&&(distance>action->copies[owner].distance||
       (distance==action->copies[owner].distance&&origin>=action->copies[owner].source_slot)))return;
    u32 candidates[3];int n=0;
    for(int i=0;i<3;i++) {
        u32 v=b->current[i];int id=v&65535,duplicate=0;
        if(!id||protected_identity(id)||effect(id)==196||!permitted(source,id))continue;
        for(int j=0;j<n;j++)if((candidates[j]&65535)==(u32)id) {duplicate=1;if(v>candidates[j])candidates[j]=v;}
        if(!duplicate)candidates[n++]=v;
    }
    if(!n)return;
    int chosen=n==1?0:FN(0x022eaa98,int(*)(int))(n);if(chosen<0||chosen>=n)return;
    action->copies[owner].ability=candidates[chosen];action->copies[owner].distance=(u16)distance;
    action->copies[owner].source_slot=(u8)origin;action->copies[owner].own_slot=(u8)own;
    action->copies[owner].entity=(u32)holder;action->copies[owner].monster=(u32)monster(holder);
}
void ME_CancelFaintCopies(u8 *m) {
    if(!ability_memory)return;
    for(int j=0;j<depth;j++)for(int i=0;i<COUNT;i++)
        if(actions[j].copies[i].monster==(u32)m)actions[j].copies[i].ability=0;
}
void ME_FlushFaintCopies(u32 token) {
    if(!ability_memory||!depth||actions[depth-1].token!=token)return;
    Action *action=&actions[depth-1];
    for(int i=0;i<COUNT;i++)if(action->copies[i].ability) {
        u8 *e=entity(i);AbilityBank *b=bank(e);int own=action->copies[i].own_slot;
        if(alive(e)&&b&&action->copies[i].entity==(u32)e&&action->copies[i].monster==(u32)monster(e)&&
           own<3&&(b->current[own]&65535)==A_POWER_OF_ALCHEMY&&ME_ClaimEffect(e,A_POWER_OF_ALCHEMY,6,0)) {
            b->current[own]=action->copies[i].ability;publish(b);
        }
        action->copies[i].ability=0;
    }
}
int ME_WanderingSwap(u8 *actor,u8 *holder) {
    if(actor==holder||!alive(actor)||!monster(holder)||!adjacent(actor,holder)||
       !defhas(actor,holder,A_WANDERING_SPIRIT))return 0;
    AbilityBank *a=bank(actor),*b=bank(holder);
    if(!a||!b||protected_profile(a)||protected_profile(b))return 0;
    int own=-1,slots[3],n=0;
    for(int i=0;i<3;i++) {
        if((b->current[i]&65535)==A_WANDERING_SPIRIT&&own<0)own=i;
        int id=a->current[i]&65535,duplicate=0;
        if(!id||!permitted(actor,id))continue;
        for(int j=0;j<n;j++)if((a->current[slots[j]]&65535)==(u32)id) {
            duplicate=1;if(a->current[i]>a->current[slots[j]])slots[j]=i;
        }
        if(!duplicate)slots[n++]=i;
    }
    if(own<0||!n||!ME_ClaimEffect(holder,A_WANDERING_SPIRIT,5,0))return 0;
    int chosen=n==1?0:FN(0x022eaa98,int(*)(int))(n);
    if(chosen<0||chosen>=n)return 0;
    int other=slots[chosen];u32 v=a->current[other];
    a->current[other]=b->current[own];b->current[own]=v;
    publish(a);publish(b);return 1;
}
/* stat order: Atk,Def,SpAtk,SpDef,numeric Speed,Accuracy,Evasion.
 * Stored changes use the existing event services for their UI and native
 * Contrary/Simple/drop/Defiant checks; numeric Speed has its own service. */
int ME_ChangeStat(u8 *actor,u8 *target,int stat,int delta) {
    if(!alive(target)||stat<0||stat>6||!delta)return 0;
    if(stat==4) {
        if(has(target,129))delta=-delta;
        return ME_ChangeSpeed(actor,target,delta,0);
    }
    if(stat<4) {
        int defensive=stat==1||stat==3,index=stat>=2;
        u32 address=delta>0?(defensive?0x02313b08:0x0231399c):(defensive?0x02313814:0x023135fc);
        FN(address,void(*)(u8*,u8*,int,int,int,int))(actor,target,index,delta>0?delta:-delta,actor!=target,0);
        return 1;
    }
    /* Hit-chance native API only raises one step. Apply the requested delta
     * here, preserving numeric storage caps and common trait rules. */
    if(has(target,129))delta=-delta;
    if(delta<0 && actor!=target && (has(target,15)||(stat==5&&has(target,30))))return 0;
    if(has(target,97))delta*=2;
    u8 *m=monster(target);int off=stat==5?0x2c:0x2e,old=U16(m,off);
    U16(m,off)=(u16)clamp(old+delta,4,16);return old!=U16(m,off);
}
int ME_HighestStat(u8 *e) {
    u8 *m=monster(e);if(!m)return 0;
    int best=0,value=-1;
    for(int i=0;i<5;i++) {
        int n=i==4?FN(ENTITY_SPEED,int(*)(u8*))(e):FN(FROM_MONSTER_FN,int(*)(u8*,int,int))(m,i>=2,i==1||i==3);
        if(n>value)value=n,best=i;
    }
    return best;
}
int ME_SpeedBonus(u8 *e) {
    int w=ME_ApparentWeather(e),bonus=0;u8 *m=monster(e);
    if(w==1&&has(e,74))bonus+=2;
    if(w==4&&has(e,27))bonus+=2;
    if(w==2&&has(e,132))bonus+=2;
    if(w==5&&has(e,145))bonus+=2;
    if(m&&!(BYTE(m,0x62)&1)&&has(e,84))bonus+=2;
    return bonus;
}
int ME_ConvertType(u8 *e,int type,u8 *move) {
    Extra *x=ext(e);
    if(x)x->conversion_valid=0;
    if(type!=1||!move)return type;
    /* The current ability slots give a deterministic priority. Conversion only
     * examines the resolved type, after Weather Ball/Hidden Power handling. */
    static const u16 ids[]={A_DRAGONIZE,A_REFRIGERATE,A_AERILATE,A_PIXILATE,A_GALVANIZE};
    static const u8 types[]={15,6,10,18,5};
    int converted=type,applied=0;
    for(int j=0;j<3&&!applied;j++) {
        int id=ME_GetAbility(e,j,1)&65535;
        if(effect(id)==107)applied=1;
        for(int i=0;i<5&&!applied;i++)if(id==ids[i])converted=types[i],applied=1;
    }
    if(x&&applied&&ability_memory&&depth) {
        x->conversion_action=actions[depth-1].token;x->conversion_move=U16(move,4);
        x->conversion_type=(u8)converted;x->conversion_valid=1;
    }
    return converted;
}
/* Additional final damage rules; existing audited ability multipliers remain
 * in their original stat/power/type locations rather than being approximated. */
void ME_AdjustDamage(u8 *a,u8 *b,u8 *damage,int type,int move) {
    int value=(int)U32(damage,0);if(value<=0)return;
    int category=FN(0x020151c8,int(*)(int))(move);
    if(category==2)return;
    if(stakeout_ready(a,b))value=multiply(value,6,5);
    static const u16 boosters[]={A_STEELWORKER,A_DRAGONS_MAW,A_TRANSISTOR,A_FIRE_MANE};
    static const u8 types[]={17,15,5,2};
    for(int i=0;i<4;i++)if(type==types[i]&&has(a,boosters[i]))value=multiply(value,6,5);
    Extra *x=ext(a);
    if(x&&x->conversion_valid&&ability_memory&&depth&&
       x->conversion_action==actions[depth-1].token&&x->conversion_move==move&&x->conversion_type==type)
        value=multiply(value,6,5);
    if(category==0&&has(a,A_TOXIC_BOOST)&&monster(a)&&
       (BYTE(monster(a),0xbf)==2||BYTE(monster(a),0xbf)==3))value=multiply(value,3,2);
    if(category==1&&has(a,A_FLARE_BOOST)&&monster(a)&&BYTE(monster(a),0xbf)==1)value=multiply(value,3,2);
    if(type==6&&defhas(a,b,95))value=multiply(value,1,2);
    if(category==0&&adjacent(a,b)&&defhas(a,b,A_AURA_GUARD))value=multiply(value,1,2);
    if(friends(a,b)&&defhas(a,b,A_TELEPATHY))value=0;
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i);
        if(e!=a&&alive(e)&&friends(e,a)&&adjacent(e,a)&&has(e,A_POWER_SPOT)) {value=multiply(value,6,5);break;}
    }
    /* Existing Punk Rock defense is x0.8. Correct it to the supplied x0.5
     * at that owner's call site instead of stacking another x0.5 here. */
    if(type==5&&x&&has(a,157)&&(x->charged||
       (ability_memory&&depth&&x->charge_action==actions[depth-1].token)))value=multiply(value,3,2);
    U32(damage,0)=(u32)value;
}
void ME_NewSunlight(void) {
    if(!++sunlight_serial)++sunlight_serial;
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i);Extra *x=ext(e);
        if(alive(e)&&x&&has(e,A_PROTOSYNTHESIS)&&ME_ApparentWeather(e)==1&&x->sun_serial!=sunlight_serial) {
            x->sun_serial=sunlight_serial;x->sun_seen=1;ME_ChangeStat(e,e,ME_HighestStat(e),1);
        }
    }
}
void ME_FloorEntry(u8 *e) {
    Extra *x=ext(e);if(!alive(e)||!x||(x->once&1))return;x->once|=1;
    ME_PickupItem(e);
    static const u16 ids[]={A_DRIZZLE,A_DROUGHT,A_SAND_STREAM,A_SNOW_WARNING,A_PRIMORDIAL_SEA,A_DESOLATE_LAND,A_DELTA_STREAM};
    static const u8 weather[]={4,1,2,5,4,1,0};
    for(int i=0;i<7;i++)if(has(e,ids[i]))ME_SetWeatherSource(e,weather[i],i>=4,ids[i]);
    /* Natural sunshine can already be active when the entity enters. A weather
     * source callback during this same entry must not award a second boost. */
    if(!x->sun_seen&&has(e,A_PROTOSYNTHESIS)&&ME_ApparentWeather(e)==1) {
        x->sun_serial=sunlight_serial;x->sun_seen=1;ME_ChangeStat(e,e,ME_HighestStat(e),1);
    }
    if(has(e,94))ME_ChangeStat(e,e,4,-3);
    if(has(e,131))U16(monster(e),0x10)=(u16)maxhp(e);
    if(has(e,A_SUPERSWEET_SYRUP)) for(int i=0;i<COUNT;i++) {
        u8 *b=entity(i);if(alive(b)&&!friends(e,b))ME_ChangeStat(e,b,6,-1);
    }
    if(has(e,222)) {
        int first=FN(0x022eaa98,int(*)(int))(7),second=FN(0x022eaa98,int(*)(int))(6);
        if(first<0||first>=7||second<0||second>=6)return;
        if(second>=first)second++;
        ME_ChangeStat(e,e,first,2);ME_ChangeStat(e,e,second,-1);
    }
}
static int healer_status(u8 *e) {
    u8 *m=monster(e);if(!m)return 0;
    int sleep=BYTE(m,0xbd),burn=BYTE(m,0xbf);
    return sleep==1||sleep==3||sleep==5||(burn>=1&&burn<=5)||
        BYTE(m,0xd0)==2||BYTE(m,0xc4)==1;
}
int ME_HealAlly(u8 *e) {
    if(!alive(e)||!has(e,A_HEALER))return 0;
    u8 *candidates[COUNT];int n=0;
    for(int i=0;i<COUNT;i++) {
        u8 *b=entity(i);
        if(b!=e&&alive(b)&&friends(e,b)&&adjacent(e,b)&&healer_status(b))candidates[n++]=b;
    }
    if(!n||!FN(0x022eab20,int(*)(int))(50))return 0;
    int selected=FN(0x022eaa98,int(*)(int))(n);if(selected<0||selected>=n)return 0;
    u8 *target=candidates[selected],*m=monster(target);
    int sleep=BYTE(m,0xbd),burn=BYTE(m,0xbf);
    /* Class-specific native cures preserve taunt, encore, sleepless, rooting,
     * binding and other conditions outside the user's seven-status list.
     * Sleep's actual ABI has five arguments: disable nightmare damage and
     * napping's optional healing rather than passing uninitialized flags. */
    if(sleep==1||sleep==3||sleep==5)
        FN(0x02305fdc,void(*)(u8*,u8*,int,int,int))(e,target,0,0,0);
    if(burn>=1&&burn<=5)FN(0x023061a8,void(*)(u8*,u8*))(e,target);
    if(BYTE(m,0xd0)==2)FN(0x023063d4,void(*)(u8*,u8*))(e,target);
    if(BYTE(m,0xc4)==1)FN(0x02306258,void(*)(u8*,u8*,int))(e,target,1);
    return 1;
}
void ME_TurnTick(u8 *e) {
    if(!alive(e))return;
    ME_FloorEntry(e);Extra *x=ext(e);
    if(x)prune_tailwind(x,monster(e));
    if(x&&x->charged)x->charged--;
    ME_HealAlly(e);
}
void ME_FaintEvent(u8 *fainted,int move,u8 *actor) {
    for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i);if(e==fainted||!alive(e))continue;
        queue_faint_copy(e,fainted);
        if(room(e,fainted)&&has(e,209)&&ME_ClaimEffect(e,209,2,0))ME_ChangeStat(e,e,2,1);
        if(e==actor && actor!=fainted && !friends(e,fainted) && move>=0 && move<=559 &&
           FN(0x020151c8,int(*)(int))(move)!=2 && ability_memory && depth && actions[depth-1].actor==(u32)actor) {
            if(has(e,170))ME_ChangeStat(e,e,0,1);
            if(has(e,A_PROTOSYNTHESIS)&&ME_ClaimEffect(e,A_PROTOSYNTHESIS,3,0))ME_ChangeStat(e,e,ME_HighestStat(e),1);
        }
    }
}
void ME_HitEvent(u8 *a,u8 *b,int previous_hp,int type,int move) {
    if(move<0||move>559||previous_hp<=hp(b)||!monster(a)||!monster(b))return;
    if(stakeout_ready(a,b)&&FN(0x020151c8,int(*)(int))(move)!=2)ext(a)->stake_used[slot(b)]=ext(b)->moved_epoch;
    Extra *attacker=ext(a);
    if(attacker&&!attacker->locked_move&&move!=355&&move!=352&&
       FN(0x020151c8,int(*)(int))(move)!=2&&has(a,A_GORILLA_TACTICS))
        attacker->locked_move=(u16)(move+1);
    if(type==5&&attacker&&attacker->charged&&has(a,157)) {
        attacker->charged=0;
        attacker->charge_action=ability_memory&&depth?actions[depth-1].token:0;
    }
    int physical=FN(0x020151c8,int(*)(int))(move)==0;
    int close=physical&&adjacent(a,b);
    if(close) {
        static const u16 thorns[]={A_ROUGH_SKIN,A_IRON_BARBS};
        for(int i=0;i<2;i++)if(has(b,thorns[i])&&ME_ClaimEffect(b,thorns[i],4,0)) {
            u8 damage[0x14];zero(damage,sizeof(damage));
            /* Fixed-damage wrapper forwards seven stack args, including the
             * two undocumented response flags. Retaliation does not trigger
             * another contact response. Keep both explicit rather than reading
             * arbitrary words past the C call frame. */
            FN(0x0230d3f4,int(*)(u8*,u8*,int,int,u8*,int,int,int,int,int,int))
                (b,a,clamp(divide(maxhp(a),8),1,32767),0,damage,0,3,563,0,0,0);
        }
        if(has(b,180)&&ME_ClaimEffect(b,180,4,0))ME_ChangeStat(b,a,4,-1);
    }
    if(physical&&has(b,A_WEAK_ARMOR)&&ME_ClaimEffect(b,A_WEAK_ARMOR,4,0)) {ME_ChangeStat(b,b,1,-1);ME_ChangeStat(b,b,4,1);}
    if(has(b,198)&&ME_ClaimEffect(b,198,4,0))ME_ChangeStat(b,b,1,1);
    if((type==12||type==14||type==16)&&has(b,A_RATTLED)&&ME_ClaimEffect(b,A_RATTLED,4,0))ME_ChangeStat(b,b,4,3);
    if(has(b,157)) {Extra *x=ext(b);if(x)x->charged=5;}
    Extra *x=ext(b);
    if(x&&!(x->once&2)&&previous_hp*2>maxhp(b)&&hp(b)*2<=maxhp(b)&&has(b,169)) {x->once|=2;ME_ChangeStat(b,b,2,1);}
    if(close)ME_WanderingSwap(a,b);
    ME_RunAway(a,b,previous_hp);
}
int ME_StatusBlocked(u8 *actor,u8 *target,int status) {
    if(!monster(target))return 0;
    if(status==12)status=0;
    if(status>=0&&status<=6&&defhas(actor,target,A_COMATOSE))return 1;
    if(status==0||status==7) {
        for(int i=0;i<COUNT;i++) {u8 *e=entity(i);if(alive(e)&&friends(e,target)&&(e==target||room(e,target))&&has(e,A_SWEET_VEIL))return 1;}
    }
    if(status>=8&&status<=11) {
        for(int i=0;i<COUNT;i++) {u8 *e=entity(i);if(alive(e)&&friends(e,target)&&(e==target||room(e,target))&&has(e,A_AROMA_VEIL))return 1;}
    }
    return 0;
}
int ME_SleepTarget(u8 *e) {
    if(!monster(e))return 0;
    return has(e,A_COMATOSE)||FN(0x023007a8,int(*)(u8*))(e);
}
int ME_TrapAvoid(u8 *e) {return has(e,A_LIGHT_METAL)&&FN(0x022eab20,int(*)(int))(50);}
int ME_Weight(u8 *e,int weight) {
    int light=has(e,A_LIGHT_METAL),heavy=has(e,A_HEAVY_METAL);
    if(light&&!heavy)weight=divide(weight,2);
    if(heavy&&!light)weight*=2;
    return weight;
}
/* PMD's MD +0x28 stores the weight-dependent damage multiplier (8 fractional
 * bits), not main-series kilograms. Modify that native reference value at the
 * weight move's lookup boundary; leave MD and non-move species lookups alone. */
int ME_WeightForMove(u8 *actor,u8 *target,int multiplier) {
    int light=defhas(actor,target,A_LIGHT_METAL),heavy=defhas(actor,target,A_HEAVY_METAL);
    if(light&&!heavy)multiplier=divide(multiplier,2);
    if(heavy&&!light)multiplier*=2;
    return clamp(multiplier,0,65535);
}
int ME_WindBlocked(u8 *actor,u8 *target,u8 *move) {
    if(!move||!alive(target)||!defhas(actor,target,A_WIND_RIDER))return 0;
    int wind=0,id=U16(move,4);
    for(unsigned i=0;i<sizeof(wind_damage_moves)/sizeof(wind_damage_moves[0]);i++)
        if(id==wind_damage_moves[i])wind=1;
    if(!wind)return 0;
    if(ME_ClaimEffect(target,A_WIND_RIDER,8,actor))ME_ChangeStat(target,target,0,1);
    return 1;
}

int ME_AbilityStat(u8 *m,int value,int defense,int index) {
    value=ME_WeatherDefense(m,value,defense);
    if(calculation_context&&defhas(calculations[calculation_context-1].actor,
                                  calculations[calculation_context-1].target,103))return value;
    if(calculation_context&&!defense&&!index)for(int i=0;i<COUNT;i++) {
        u8 *e=entity(i);
        if(monster(e)==m&&has(e,A_GORILLA_TACTICS))return multiply(value,3,2);
    }
    return value;
}
int ME_MoveAllowed(u8 *e,u8 *move) {
    if(!move||!has(e,A_GORILLA_TACTICS))return 1;
    Extra *x=ext(e);if(!x||!x->locked_move)return 1;
    int id=U16(move,4),locked=x->locked_move-1;
    if(id==355)return 1;
    u8 *m=monster(e);int pp=0;
    for(int i=0;i<4;i++)if((BYTE(m,0x124+i*8)&1)&&U16(m,0x128+i*8)==locked)pp+=BYTE(m,0x12a+i*8);
    if(!pp)return id==352?2:0;
    return id==locked;
}
int ME_RedirectBlocked(u8 *actor) {return has(actor,A_STALWART);}
int ME_ForcedMoveBlocked(u8 *actor,u8 *target) {return defhas(actor,target,A_HEAVY_METAL);}
void ME_FreeAbilities(void) {
    if(ability_memory)FN(0x02001188,void(*)(void*))(ability_memory);
    ability_memory=0;
    if(extra)FN(0x02001188,void(*)(void*))(extra);
    extra=0;sunlight_serial=0;movement_serial=0;state.magic=0;movement_context=0;calculation_context=0;speed_move_context=0;
    zero(calculations,sizeof(calculations));
}

int ME_EnterMovement(void) {int old=movement_context;movement_context=1;return old;}
void ME_LeaveMovement(int previous) {movement_context=previous;}
int ME_EnterCalculation(u8 *actor,u8 *target) {
    int previous=calculation_context;
    if(previous<16) {calculations[previous].actor=actor;calculations[previous].target=target;calculation_context++;}
    return previous;
}
void ME_LeaveCalculation(int previous) {
    if(previous>=0&&previous<16&&calculation_context==previous+1) {
        zero(&calculations[previous],sizeof(Calculation));calculation_context=previous;
    }
}
int ME_LegacyAbilityActive(u8 *e,int id,u32 caller) {
    ensure();if(!ability_memory)return 0;
    if(id==43&&(caller==0x022fa9d8||caller==0x02301604||caller==0x023016fc))return 0;
    if(movement_context&&(id==27||id==74||id==84||id==132||id==145||id==94))return 0;
    if((calculation_context||depth)&&(id==18||id==180||id==198||id==169||id==157||id==170||id==209))return 0;
    if(id==107&&(depth||calculation_context||caller==0x023022b4))return 0;
    return ME_AbilityActive(e,id);
}
int ME_QuickFeet(u8 *a,u8 *b) {if(!has(b,109))return 0;ME_ChangeStat(a,b,4,1);return 1;}
void ME_MotorDrive(u8 *e) {ME_ChangeStat(e,e,4,1);}
void ME_Steadfast(u8 *a,u8 *b) {if(has(b,112))ME_ChangeStat(a,b,4,1);}
u32 ME_BeginUserAction(u8 *e,int index) {
    u8 *m=monster(e);if(!m)return 0;
    int move=index>=0&&index<4?U16(m,0x128+index*8):355;
    return ME_BeginAction(e,move);
}
void ME_FaintBoundary(u8 *e,int move,u8 *actor) {
    u32 token=0;
    if(!ability_memory||!depth)token=ME_BeginAction(actor&&monster(actor)?actor:e,move);
    ME_FaintEvent(e,move,actor);
    if(token)ME_EndAction(token);
}
